import threading
import Queue
import time
import copy
import logging

_logger = logging.getLogger("dtm.loadBalancing")


DTM_ASK_FOR_TASK_DELAY = 2.5
DTM_SEND_TASK_DELAY = 0.001
DTM_RESTART_QUEUE_BLOCKING_FROM = 1.

class DtmLoadBalancer(object):
    """
    """
    def __init__(self, workersIterator, workerId, execQueue, randomizer):
        self.wid = workerId
        self.ws = {}
        self.execQ = execQueue      # Les autres queues ne sont pas necessaires
        self.wIter = workersIterator
        self.dLock = threading.Lock()
        self.tmpRecvJob = False
        self.localRandom = randomizer

        for w in workersIterator:
            self.ws[w] = [0.,0.,0.,0.,0, False, []]
            """
            [Load_current_exec, Load_execQueue, Load_WaitingForRestart,
            Load_Waiting, numero de sequence de derniere mise a jour, temps de derniere comm, en attente d'un/des ACK]
            """
        self.totalExecLoad, self.totalEQueueLoad, self.totalWaitingRQueueLoad, self.totalWaitingQueueLoad = 0., 0., 0., 0.
        self.sendDelayMultiplier = DTM_SEND_TASK_DELAY*float(len(self.ws))**0.5
        self.lastTaskSend = time.time() - self.sendDelayMultiplier
        self.lastQuerySend = time.time()
        
    def getNodesDict(self):
        return self.ws

    def updateSelfStatus(self, statusTuple):
        self.ws[self.wid][0:4] = statusTuple
        self.ws[self.wid][4] += 1

    def mergeNodeStatus(self, otherDict):
        for wId in otherDict:
            if len(self.ws[wId][6]) == 0 and otherDict[wId][4] > self.ws[wId][4] and wId != self.wid:
                self.ws[wId][:5] = otherDict[wId][:5]   # Les deux dernieres infos sont "personnelles"
    
    def notifyTaskReceivedFrom(self, fromId):
        self.ws[fromId][5] = True
        self.tmpRecvJob = True

    def acked(self, fromWorker, ackN):
        try:
            self.ws[fromWorker][6].remove(ackN)
        except ValueError:
            print("ERROR : Tentative to delete an already received or non-existant ACK!", self.ws[fromWorker][6], ackN)

    def takeDecision(self):
    #print("TAKE DECISION CALLED ON WORKER " + str(self.wid) + " with thread " + str(threading.currentThread()))

        MAX_PROB = 1.
        MIN_PROB = 0.00

        sendTasksList = []
        sendNotifList = []

        listLoads = self.ws.values()
        self.totalExecLoad, self.totalEQueueLoad, self.totalWaitingRQueueLoad, self.totalWaitingQueueLoad = 0., 0., 0., 0.
        totalSum2 = 0.
        for r in listLoads:
            self.totalExecLoad += r[0]
            self.totalEQueueLoad += r[1]
            self.totalWaitingRQueueLoad += r[2]
            self.totalWaitingQueueLoad += r[3]
            totalSum2 += (r[0]+r[1]+r[2])**2

        avgLoad = (self.totalExecLoad + self.totalEQueueLoad + self.totalWaitingRQueueLoad) / float(len(self.ws))
        if totalSum2/float(len(self.ws)) - avgLoad**2 < 0:
            # Cas bizarre, il faudra investiguer...
            stdDevLoad = 0
        else:
            stdDevLoad = (totalSum2/float(len(self.ws)) - avgLoad**2)**0.5
        selfLoad = sum(self.ws[self.wid][:3])
        diffLoad = selfLoad - avgLoad

        #if sum(self.ws[self.wid][:3]) == 0.:
      #print(sum([len(x[6]) for x in self.ws.values()]))
        #print(str(time.clock()) + " ["+str(self.wid)+"] has a load of " + str(sum(self.ws[self.wid][:3])) + " (avg : "+str(avgLoad)+")")

        listPossibleSendTo = filter(lambda d: d[1][5] and sum(d[1][:3]) > avgLoad, self.ws.items())
        if selfLoad == 0 and len(listPossibleSendTo) > 0 and avgLoad != 0 and self.ws[self.wid][2] < DTM_RESTART_QUEUE_BLOCKING_FROM:
            # Algorithme d'envoi de demandes de taches
            self.lastQuerySend = time.time()
            for worker in listPossibleSendTo:
                sendNotifList.append(worker[0])
                self.ws[worker[0]][5] = False

           
        if self.ws[self.wid][1] > 0 and diffLoad > -stdDevLoad and avgLoad != 0\
            and stdDevLoad != 0\
            and time.time()-self.lastTaskSend > self.sendDelayMultiplier:
            # Algorithme d'envoi de taches
            def scoreFunc(loadi):
                if loadi < (avgLoad-2*stdDevLoad):
                    return MAX_PROB    # Si le load du worker est vraiment tres bas, forte probabilite de lui envoyer des taches
                elif loadi > (avgLoad + stdDevLoad):
                    return MIN_PROB    # Si le load du worker est tres haut, tres faible probabilite de lui envoyer des taches
                else:
                    a = (MIN_PROB-MAX_PROB)/(3*stdDevLoad)
                    b = MIN_PROB - a*(avgLoad + stdDevLoad)
                    return a*loadi + b      # Lineaire entre Avg-2*stdDev et Avg+stdDev

            scores = [(None,0)] * (len(self.ws)-1)      # Gagne-t-on vraiment du temps en prechargeant la liste?
            i = 0
            for worker in self.ws:
                if worker == self.wid:
                    continue
                scores[i] = (worker, scoreFunc(sum(self.ws[worker][:3])))
                i += 1
                
            while diffLoad > 0.00000001 and len(scores) > 0 and self.ws[self.wid][1] > 0.:
                selectedIndex = self.localRandom.randint(0,len(scores)-1)
                if self.localRandom.random() > scores[selectedIndex][1]:
                    del scores[selectedIndex]
                    continue

                widToSend = scores[selectedIndex][0]

                loadForeign = self.ws[widToSend]
                diffLoadForeign = sum(loadForeign[:3]) - avgLoad
                sendT = 0.

                if diffLoadForeign < 0:     # On veut lui envoyer assez de taches pour que son load = loadAvg
                    sendT = diffLoadForeign*-1 if diffLoadForeign*-1 < self.ws[self.wid][1] else self.ws[self.wid][1]
                elif diffLoadForeign < stdDevLoad:  # On veut lui envoyer assez de taches pour son load = loadAvg + stdDev
                    sendT = stdDevLoad - diffLoadForeign if stdDevLoad - diffLoadForeign < self.ws[self.wid][1] else self.ws[self.wid][1]
                else:               # On envoie une seule tache
                    sendT = 0.

                tasksIDs, retiredTime = self.execQ.getTasksIDsWithExecTime(sendT)
                tasksObj = []
                for tID in tasksIDs:
                    t = self.execQ.getSpecificTask(tID)
                    if not t is None:
                        tasksObj.append(t)

                if len(tasksObj) > 0:
                    diffLoad -= retiredTime
                    self.ws[self.wid][1] -= retiredTime
                    self.ws[widToSend][1] += retiredTime

                    ackNbr = len(self.ws[widToSend][6])
                    self.ws[widToSend][6].append(ackNbr)

                    sendTasksList.append((widToSend, tasksObj, ackNbr))

                del scores[selectedIndex]       # On s'assure de ne pas reprendre le meme worker
                
            self.lastTaskSend = time.time()
        return sendNotifList, sendTasksList