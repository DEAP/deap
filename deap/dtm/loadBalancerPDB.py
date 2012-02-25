#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

import threading
try:
    import Queue
except ImportError:
    import queue as Queue
import time
import copy
import logging

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        # Python 2.5
        import xml.etree.ElementTree as etree

_logger = logging.getLogger("dtm.loadBalancing")


DTM_ASK_FOR_TASK_DELAY = 2.5
DTM_SEND_TASK_DELAY = 0.001
DTM_RESTART_QUEUE_BLOCKING_FROM = 1.

class LoadInfoContainer(object):
    """
    Contains load information of a worker
    """
    __slots__ = ('loadCurrentExec',     # Load of the current exec task
                'loadExecQ',            # Load of the exec queue
                'loadWaitingRestartQ',  # Load of the waiting for restart queue
                'loadWaitingQ',         # Load of the waiting queue
                'seqNbr',               # Sequence number, only ++ by the worker which is its info
                'infoUpToDate',         # Boolean : is the dictionnary of the OTHER worker up to date with our info?
                'ackWaiting')           # List of ACKs (messages transmitted)
    def __init__(self,args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self,state):
        for t in state:
            self.__setattr__(t,state[t])
    def sumRealLoad(self):
        return self.loadCurrentExec+self.loadExecQ+self.loadWaitingRestartQ

class LoadBalancer(object):
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
        self.xmlLogger = None

        for w in workersIterator:
            self.ws[w] = LoadInfoContainer({'loadCurrentExec' : 0.,
                                            'loadExecQ' : 0.,
                                            'loadWaitingRestartQ' : 0.,
                                            'loadWaitingQ' : 0.,
                                            'seqNbr' : 0.,
                                            'infoUpToDate' : False,
                                            'ackWaiting' : []})

        self.totalExecLoad, self.totalEQueueLoad, self.totalWaitingRQueueLoad, self.totalWaitingQueueLoad = 0., 0., 0., 0.
        self.sendDelayMultiplier = DTM_SEND_TASK_DELAY*float(len(self.ws))**0.5
        self.lastTaskSend = time.time() - self.sendDelayMultiplier
        self.lastQuerySend = time.time()
    
    def setTraceModeOn(self, xmlLogger):
        self.xmlLogger = xmlLogger
    
    def getNodesDict(self):
        return self.ws

    def updateSelfStatus(self, statusTuple):
        self.ws[self.wid].loadCurrentExec = statusTuple[0]
        self.ws[self.wid].loadExecQ = statusTuple[1]
        self.ws[self.wid].loadWaitingRestartQ = statusTuple[2]
        self.ws[self.wid].loadWaitingQ = statusTuple[3]       
        self.ws[self.wid].seqNbr += 1

    def mergeNodeStatus(self, otherDict):
        for wId in otherDict:
            if len(self.ws[wId].ackWaiting) == 0 and otherDict[wId].seqNbr > self.ws[wId].seqNbr and wId != self.wid:
                remInfoUpToDate = self.ws[wId].infoUpToDate                
                self.ws[wId] = otherDict[wId]   # Les deux dernieres infos sont "personnelles"
                self.ws[wId].infoUpToDate = remInfoUpToDate
                self.ws[wId].ackWaiting = []
    
    def notifyTaskReceivedFrom(self, fromId):
        self.ws[fromId].infoUpToDate = True
        self.tmpRecvJob = True

    def acked(self, fromWorker, ackN):
        try:
            self.ws[fromWorker].ackWaiting.remove(ackN)
        except ValueError:
            print("ERROR : Tentative to delete an already received or non-existant ACK!", self.ws[fromWorker].ackWaiting, ackN)

    def takeDecision(self):
        MAX_PROB = 1.
        MIN_PROB = 0.00

        sendTasksList = []
        sendNotifList = []
        
        if not self.xmlLogger is None:
            decisionLog = etree.SubElement(self.xmlLogger, "decision", {"time" : repr(time.time()), 
                                                                        "selfLoad" : repr(self.ws[self.wid].loadCurrentExec)+","+repr(self.ws[self.wid].loadExecQ)+","+repr(self.ws[self.wid].loadWaitingRestartQ)+","+repr(self.ws[self.wid].loadWaitingQ)})
            for workerId in self.ws:
                etree.SubElement(decisionLog, "workerKnownState", {"id" : repr(workerId), "load" : repr(self.ws[workerId].loadCurrentExec)+","+repr(self.ws[workerId].loadExecQ)+","+repr(self.ws[workerId].loadWaitingRestartQ)+","+repr(self.ws[workerId].loadWaitingQ)})

        listLoads = self.ws.values()
        self.totalExecLoad, self.totalEQueueLoad, self.totalWaitingRQueueLoad, self.totalWaitingQueueLoad = 0., 0., 0., 0.
        totalSum2 = 0.
        for r in listLoads:
            self.totalExecLoad += r.loadCurrentExec
            self.totalEQueueLoad += r.loadExecQ
            self.totalWaitingRQueueLoad += r.loadWaitingRestartQ
            self.totalWaitingQueueLoad += r.loadWaitingQ
            totalSum2 += (r.loadCurrentExec+r.loadExecQ+r.loadWaitingRestartQ)**2

        avgLoad = (self.totalExecLoad + self.totalEQueueLoad + self.totalWaitingRQueueLoad) / float(len(self.ws))
        try:
            stdDevLoad = (totalSum2/float(len(self.ws)) - avgLoad**2)**0.5
        except ValueError:
            # Some weird cases with floating point precision, where avgLoad**2 might be an epsilon greater than totalSum2/len(self.ws)
            stdDevLoad = 0.
        selfLoad = self.ws[self.wid].sumRealLoad()
        diffLoad = selfLoad - avgLoad


        listPossibleSendTo = filter(lambda d: d[1].infoUpToDate and d[1].sumRealLoad() > avgLoad, self.ws.items())
        if selfLoad == 0 and len(listPossibleSendTo) > 0 and avgLoad != 0 and self.ws[self.wid].loadWaitingRestartQ < DTM_RESTART_QUEUE_BLOCKING_FROM:
            # Algorithme d'envoi de demandes de taches
            self.lastQuerySend = time.time()
            txtList = ""
            for worker in listPossibleSendTo:
                sendNotifList.append(worker[0])
                txtList +=str(worker[0])+","
                self.ws[worker[0]].infoUpToDate = False
                
            if not self.xmlLogger is None:
                etree.SubElement(decisionLog, "action", {"time" : repr(time.time()), "type" : "sendrequest", "destination":txtList})

           
        if self.ws[self.wid].loadExecQ > 0 and diffLoad > -stdDevLoad and avgLoad != 0 and stdDevLoad != 0:
            # Algorithme d'envoi de taches
            def scoreFunc(loadi):
                if loadi < (avgLoad-2*stdDevLoad) or loadi == 0:
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
                scores[i] = (worker, scoreFunc(self.ws[worker].sumRealLoad()))
                i += 1
            
            if not self.xmlLogger is None:
                 etree.SubElement(decisionLog, "action", {"time" : repr(time.time()), "type" : "checkavail", "destination":str(scores)})
            
            while diffLoad > 0.00000001 and len(scores) > 0 and self.ws[self.wid].loadExecQ > 0.:
                selectedIndex = self.localRandom.randint(0,len(scores)-1)
                if self.localRandom.random() > scores[selectedIndex][1]:
                    del scores[selectedIndex]
                    continue

                widToSend = scores[selectedIndex][0]

                loadForeign = self.ws[widToSend]
                diffLoadForeign = loadForeign.sumRealLoad() - avgLoad
                sendT = 0.

                if diffLoadForeign < 0:     # On veut lui envoyer assez de taches pour que son load = loadAvg
                    sendT = diffLoadForeign*-1 if diffLoadForeign*-1 < self.ws[self.wid].loadExecQ else self.ws[self.wid].loadExecQ
                elif diffLoadForeign < stdDevLoad:  # On veut lui envoyer assez de taches pour son load = loadAvg + stdDev
                    sendT = stdDevLoad - diffLoadForeign if stdDevLoad - diffLoadForeign < self.ws[self.wid].loadExecQ else self.ws[self.wid].loadExecQ
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
                    self.ws[self.wid].loadExecQ -= retiredTime
                    self.ws[widToSend].loadExecQ += retiredTime

                    ackNbr = len(self.ws[widToSend].ackWaiting)
                    self.ws[widToSend].ackWaiting.append(ackNbr)

                    sendTasksList.append((widToSend, tasksObj, ackNbr))

                del scores[selectedIndex]       # On s'assure de ne pas reprendre le meme worker
                        
            if not self.xmlLogger is None:
                etree.SubElement(decisionLog, "action", {"time" : repr(time.time()), "type" : "sendtasks", "destination":str([b[0] for b in sendTasksList])[1:-1], "tasksinfo" : str([len(b[1]) for b in sendTasksList])[1:-1]})
                
            self.lastTaskSend = time.time()
        return sendNotifList, sendTasksList