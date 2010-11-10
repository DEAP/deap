import threading
import time
import math
import pickle
import random
import Queue
import copy


# Constantes
DTM_MPI_LATENCY = 0.01
DTM_CONTROL_THREAD_LATENCY = 0.005
DTM_ASK_FOR_TASK_DELAY = 0.5
DTM_RESTART_QUEUE_BLOCKING_FROM = 1.

DTM_LB_AGRESSIVITY = 0.1
DTM_LB_DEFAULT_RELTIME = 1


MSG_COMM_TYPE = 0
MSG_SENDER_INFO = 1
MSG_NODES_INFOS = 2


def erf(x):
    try:    # math.erf() is implemented only since Python 2.7
        return math.erf(x)
    except AttributeError:
        # See http://stackoverflow.com/questions/457408/is-there-an-easily-available-implementation-of-erf-for-python
        # save the sign of x
        sign = 1
        if x < 0:
            sign = -1
        x = abs(x)

        # constants
        a1 =  0.254829592
        a2 = -0.284496736
        a3 =  1.421413741
        a4 = -1.453152027
        a5 =  1.061405429
        p  =  0.3275911

        # A&S formula 7.1.26
        t = 1.0/(1.0 + p*x)
        y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*math.exp(-x*x)
        return sign*y # erf(-x) = -erf(x)


def _printDtmMsg(msg, gravity=1):
    print("#--------------- DTM ---------------#")
    print("# " + msg + "\n")


class DtmTaskIdGenerator(object):
    """
    A thread-safe ID generator.
    A DTM task ID is a tuple looking like (workerId, uniqId)
    With MPI, workerId is an integer (rank) and the uniqIds start from 0,
    but workerId can be virtually any immutable object (as it is used as
    a dictionnary key)
    """
    def __init__(self, rank, initId=0):
        self.r = rank
        self.wtid = 0
        self.generatorLock = threading.Lock()

    @property
    def tid(self):
        self.generatorLock.acquire()
        newId = self.wtid
        self.wtid += 1
        self.generatorLock.release()
        return (self.r, newId)


class DtmExecInfo(object):
    """
    Contient l'information sur la tache en cours d'execution,
    et un lock global pour cette execution
    """
    def __init__(self, tStats, tStatsLock):
        self.eLock = threading.Lock()
        self.tStats = tStats
        self.tStatsLock = tStatsLock
        self.eCurrent = None
        self.mainThread = threading.currentThread()
        self.piSqrt = math.sqrt(math.pi)
        self.sqrt2 = 2**0.5

    def _execTimeRemaining(self, mean, stdDev, alreadyDone):
        if alreadyDone == 0.:
            # On a pas encore commence a executer : donc c'est la moyenne
            return mean

        # Sinon, on calcule le centre de masse de la portion de la gaussienne restante
        # Par exemple, si on a une gaussienne de parametres (mu, sigma) = (3, 4)
        # et que la tache en est a sa troisieme (3) seconde d'execution
        # Alors on peut estimer qu'elle devrait terminer vers :
        # int(x*gaussienne) / int(gaussienne) sur l'intervalle [3, +infini]
        # ou int est une INTEGRALE
        #
        # Ce qui donne 6.192 secondes, soit un temps restant de 6.192 - 3 = 3.192 s.
        #

        # Evaluation de la primitive au point 'alreadyDone'
        commonPart = erf(self.sqrt2*(alreadyDone - mean)/(stdDev * 2))
        areaPart1 = 0.5*commonPart
        massCenterPart1 = (self.sqrt2/(4*self.piSqrt)) * (-2*stdDev*math.exp(-0.5*((alreadyDone-mean)**2)/(stdDev**2)) + mean*(self.piSqrt)*(self.sqrt2)*commonPart)

        # Evaluation de la primitive au point 'infini'
        # erf(+inf) = 1, donc
        areaPart2 = 0.5
        # exp(-inf) = 0, et erf(+inf) = 1, donc
        massCenterPart2 = mean/2.

        previsionPoint = (massCenterPart2 - massCenterPart1)/(areaPart2 - areaPart1)

        return previsionPoint - alreadyDone


    def acquire(self, blocking=True):
        if self.eLock.acquire(blocking):
            self.eCurrent = threading.currentThread()
            return True
        else:
            return False

    def isLocked(self):
        if self.eLock.acquire(False):
            self.eLock.release()
            return False
        return True

    def release(self):
        self.eCurrent = None
        self.eLock.release()

    def getLoad(self):
        try:
            self.tStatsLock.acquire()
            tInfo = self.tStats.get(self.eCurrent.t, [1,1,0,0])
            val = self._execTimeRemaining(tInfo[0], tInfo[1], self.eCurrent.timeExec)
            self.tStatsLock.release()
            return val
        except AttributeError:
            self.tStatsLock.release()
            return 0.


class DtmTaskQueue(object):
    """
    """
    def __init__(self, tasksStatsStruct, tasksStatsLock):
        self.tStats = tasksStatsStruct
        self.tStatsLock = tasksStatsLock
        self.previousLoad = 0.
        self.piSqrt = math.sqrt(math.pi)
        self.sqrt2 = 2**0.5
        self._tQueue = Queue.PriorityQueue()
        self._tDict = {}
        self._actionLock = threading.Lock()
        self.changed = True

    def _getTimeInfoAbout(self, task):
        if isinstance(task, tuple):
            target = task[7]
            timeDone = 0.
        else:
            target = task.t
            timeDone = task.timeExec

        self.tStatsLock.acquire()
        tInfo = self.tStats.get(target, [1,1,0,0])
        self.tStatsLock.release()

        return self._execTimeRemaining(tInfo[0], tInfo[1], timeDone)

    def _execTimeRemaining(self, mean, stdDev, alreadyDone):
        if alreadyDone == 0. or stdDev == 0:
            # On a pas encore commence a executer : donc c'est la moyenne
            # Ou si l'ecart type est de 0, alors ce n'est pas une gaussienne
            # Ce dernier cas arrive pour les temps d'execution des threads gerant
            # les taches asynchrones
            return mean

        # Sinon, on calcule le centre de masse de la portion de la gaussienne restante
        # Par exemple, si on a une gaussienne de parametres (mu, sigma) = (3, 4)
        # et que la tache en est a sa troisieme (3) seconde d'execution
        # Alors on peut estimer qu'elle devrait terminer vers :
        # int(x*gaussienne) / int(gaussienne) sur l'intervalle [3, +infini]
        # ou int est une INTEGRALE
        #
        # Ce qui donne 6.192 secondes, soit un temps restant de 6.192 - 3 = 3.192 s.
        #

        # Evaluation de la primitive au point 'alreadyDone'
        commonPart = erf(self.sqrt2*(alreadyDone - mean)/(stdDev * 2))
        areaPart1 = 0.5*commonPart
        massCenterPart1 = (self.sqrt2/(4*self.piSqrt)) * (-2*stdDev*math.exp(-0.5*((alreadyDone-mean)**2)/(stdDev**2)) + mean*(self.piSqrt)*(self.sqrt2)*commonPart)

        # Evaluation de la primitive au point 'infini'
        # erf(+inf) = 1, donc
        areaPart2 = 0.5
        # exp(-inf) = 0, et erf(+inf) = 1, donc
        massCenterPart2 = mean/2.

        previsionPoint = (massCenterPart2 - massCenterPart1)/(areaPart2 - areaPart1)

        return previsionPoint - alreadyDone

    def put(self, taskObject):
        self.putList([taskObject])

    def putList(self, tasksList):
	#print("PUT LIST with " + str(len(tasksList)) + " elements, and " + str(len(self._tDict)) + " elements already")
        self._actionLock.acquire()
        for taskObject in tasksList:
            if isinstance(taskObject, tuple):
                self._tQueue.put((taskObject[5], taskObject))
                self._tDict[taskObject[0]] = taskObject
            else:
                self._tQueue.put((taskObject.timeCreation, taskObject))
                self._tDict[taskObject.tid] = taskObject
        
        #print("PUT LIST end : " + str(len(self._tDict)) + " elements in the dict")
        self.changed = True
        self._actionLock.release()

    def getTask(self):
        self._actionLock.acquire()
        while True:
            try:
                taskObject = self._tQueue.get_nowait()[1]
            except Queue.Empty:
                self._actionLock.release()
                raise Queue.Empty

            if isinstance(taskObject, tuple):
                taskId = taskObject[0]
            else:
                taskId = taskObject.tid

            if taskId in self._tDict:
                del self._tDict[taskId]
                self.changed = True
                self._actionLock.release()
                return taskObject


    def isTaskIn(self, taskId):
        return taskId in self._tDict

    def _getApproximateLoad(self):
        return self.previousLoad
    
    def getLen(self):
        return len(self._tDict)
    
    def getLoad(self):
        tmpLoad = 0.
        self._actionLock.acquire()
        if not self.changed:
            self._actionLock.release()
            return self.previousLoad
	  
        for tid,tObj in self._tDict.items():
            tmpLoad += self._getTimeInfoAbout(tObj)

        self.previousLoad = tmpLoad
        self.changed = False
        self._actionLock.release()
        return self.previousLoad

    def getSpecificTask(self, taskId):
        self._actionLock.acquire()
        if taskId in self._tDict:
            task = self._tDict[taskId]
            del self._tDict[taskId]
            self.changed = True
        else:
            task = None
        self._actionLock.release()
        return task

    def getTaskByExecTime(self, execTimeWanted, maxDiff=-1.):
        # maxDiff est la difference maximale acceptee.
        # si aucune tache ne rentre dans le maxDiff, on renvoit None
        # -1 signifie qu'il n'y a pas de difference maximale permise
        mostClose = None
        self._actionLock.acquire()

        for tid,tObj in self._tDict.items():
            timeDiff = math.abs(execTimeWanted - self._getTimeInfoAbout(tObj))
            if mostClose is None or mostClose[1] > timeDiff:
                mostClose = (tid, timeDiff)

        self._actionLock.release()

        if mostClose is None or (maxDiff >= 0 and mostClose[1] > maxDiff):
            return None
        else:
            return self.getSpecificTask(mostClose[0])

    def getTasksIDsWithExecTime(self, execTimeWanted, maxDiff=-1.):
        # Retourne une liste contenant des taches dont la duree totale
        # est approximativement egale a execTimeWanted
        returnList = []
        totalTime = 0.
        self._actionLock.acquire()

        for tid,tObj in self._tDict.items():
            timeInfo = self._getTimeInfoAbout(tObj)

            if totalTime + timeInfo <= execTimeWanted:
                returnList.append(tid)
                totalTime += timeInfo

        self._actionLock.release()
        return returnList, totalTime

class DtmLoadBalancer(object):
    """
    """
    def __init__(self, workersIterator, workerId, execQueue):
        self.wid = workerId
        self.ws = {}
        self.execQ = execQueue      # Les autres queues ne sont pas necessaires
        self.wIter = workersIterator
        self.dLock = threading.Lock()

        for w in workersIterator:
            self.ws[w] = [0.,0.,0.,0.,0, time.time(), []]
            """
            [Load_current_exec, Load_execQueue, Load_WaitingForRestart,
            Load_Waiting, numero de sequence de derniere mise a jour, temps de derniere comm, en attente d'un/des ACK]
            """
        self.totalExecLoad, self.totalEQueueLoad, self.totalWaitingRQueueLoad, self.totalWaitingQueueLoad = 0., 0., 0., 0.

    def getNodesDict(self):
        return self.ws

    def updateSelfStatus(self, statusTuple):
        self.ws[self.wid][0:4] = statusTuple
        self.ws[self.wid][4] += 1

    def mergeNodeStatus(self, otherDict):
        for wId in otherDict:
            if len(self.ws[wId][6]) == 0 and otherDict[wId][4] > self.ws[wId][4] and wId != self.wid:
                self.ws[wId][:5] = otherDict[wId][:5]   # Les deux dernieres infos sont "personnelles"

    def acked(self, fromWorker, ackN):
        try:
            self.ws[fromWorker][6].remove(ackN)
        except ValueError:
            print("ERROR : Tentative to delete an already received or non-existant ACK!", self.ws[fromWorker][6], ackN)
    
    def takeDecision(self):
    #print("TAKE DECISION CALLED ON WORKER " + str(self.wid) + " with thread " + str(threading.currentThread()))
	
        MAX_PROB = 1.
        MIN_PROB = 0.05

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
        stdDevLoad = (totalSum2/float(len(self.ws)) - avgLoad**2)**0.5
        selfLoad = sum(self.ws[self.wid][:3])
        diffLoad = selfLoad - avgLoad
        
        #if sum(self.ws[self.wid][:3]) == 0.:
	  #print(sum([len(x[6]) for x in self.ws.values()]))
        #print(str(time.clock()) + " ["+str(self.wid)+"] has a load of " + str(sum(self.ws[self.wid][:3])) + " (avg : "+str(avgLoad)+")")


        if diffLoad <= 0 and avgLoad != 0 and self.ws[self.wid][2] < DTM_RESTART_QUEUE_BLOCKING_FROM and (selfLoad == 0 or random.random() < (stdDevLoad/(avgLoad*selfLoad))):
            # Algorithme d'envoi de demandes de taches
            for wid in self.ws:
                if sum(self.ws[wid][:3]) > diffLoad and wid != self.wid and time.time() - self.ws[wid][5] > DTM_ASK_FOR_TASK_DELAY:
                    sendNotifList.append(wid)
                    self.ws[wid][5] = time.time()

        if self.ws[self.wid][1] > 0 and diffLoad > -stdDevLoad and avgLoad != 0 and stdDevLoad != 0 and random.random() < (stdDevLoad * selfLoad/(avgLoad**2)):
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

            scores = [(None,0)] * (len(self.ws)-1)
            i = 0
            for worker in self.ws:
                if worker == self.wid:
                    continue
                scores[i] = (worker, scoreFunc(sum(self.ws[worker][:3])))
                i += 1

            while diffLoad > 0.00000001 and len(scores) > 0 and self.ws[self.wid][1] > 0.:
                selectedIndex = random.randint(0,len(scores)-1)
                if random.random() > scores[selectedIndex][1]:
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
                    
                del scores[selectedIndex]

        return sendNotifList, sendTasksList



class DtmControl(object):
    """
    DtmControl is the main DTM class. The dtm object you receive when you use ``from dtm.taskmanager import dtm``
    is an instance of this class.

    Most of its methods are used by your program, in the execution tasks; however, two of thems (start() and setOptions()) MUST be called
    in the MainThread (i.e. the thread started by the Python interpreter).

    As this class is instancied directly in the module, initializer takes no arguments.
    """
    def __init__(self):
        self.sTime = time.clock()

        self.tasksStatsLock = threading.Lock()
        self.tasksStats = {None:[0,0,0,1]}

        # Lock d'execution global qui assure qu'un seul thread a la fois
        # essaie de s'executer
        # Il permet aussi de savoir au thread de controle si on execute encore quelque chose
        self.dtmExecLock = DtmExecInfo(self.tasksStats, self.tasksStatsLock)

        self.waitingThreadsQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)
        self.waitingThreads = {}
        self.waitingThreadsLock = threading.Lock()

        self.asyncWaitingList = {}
        self.asyncWaitingListLock = threading.Lock()


        self.waitingForRestartQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)
        self.execQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)

        self.recvQueue = Queue.Queue()
        self.sendQueue = Queue.Queue()

        self.exitStatus = threading.Event()

        self.commExitNotification = threading.Event()

        self.commReadyEvent = threading.Event()

        self.exitState = (None, None)
        self.exitSetHere = False

        self.commManagerType = "pympi"
        self.isStarted = False

        self.refTime = 1.

        self.loadBalancer = None



    def _doCleanUp(self):
        """
        Clean up function, called at this end of the execution.
        Should NOT be called by the user.
        """

        msgT = "Rank " + str(self.workerId) + " ("+str(threading.currentThread().name)+" / " + str(threading.currentThread().ident) + ")\n"
        for target,times in self.tasksStats.items():
            msgT += "\t" + str(target) + " : Avg=" + str(times[0]*self.refTime) + ", StdDev=" + str(times[1]*self.refTime) + " with " + str(times[3]) + " calls\n"
            #msgT += "\t" + str(target) + " : Avg=" + str(sum(times)/float(len(times))) + ", Min=" + str(min(times)) + ", Max=" + str(max(times)) + ", Total : " + str(sum(times)) + " used by " + str(len(times)) + " calls\n"
        msgT += "\n"
        _printDtmMsg(msgT)

        if self.exitSetHere:
            for n in self.commThread.iterOverIDs():
                if n == self.workerId:
                    continue
                self.sendQueue.put((n, ("Exit", self.workerId, 0, "Exit message")))

        self.commExitNotification.set()
        self.commThread.join()

        del self.execQueue
        del self.sendQueue
        del self.recvQueue

        countThreads = sum([1 for th in threading.enumerate() if not th.daemon])
        if countThreads > 1:
            print("Warning : there's more than 1 active thread at the exit (" + str(threading.activeCount()) + " total)\n" + str(threading.enumerate()))

        if self.commThread.isRootWorker:
            _printDtmMsg("Total execution time : " + str(time.clock() - self.sTime))



    def _addTaskStat(self, taskKey, timeExec):
        # On exprime le temps d'execution d'une tache en reference au temps de calibration
        comparableLoad = timeExec / self.refTime
        # On ne conserve pas tous les temps d'execution
        # La moyenne et l'ecart type sont mis a jour en temps reel
        self.tasksStatsLock.acquire()
        if not taskKey in self.tasksStats:
            # [0] : Moyenne des temps d'exec RELATIFS, [1] ecart-type de ces temps d'exec, [2] somme au carre, [3] : Nbr d'executions
            self.tasksStats[taskKey] = [timeExec, 0., timeExec*timeExec, 1]
        else:
            oldAvg, oldStdDev, oldSum2, oldExecCount = self.tasksStats[taskKey]
            newAvg = (timeExec + oldAvg*oldExecCount)/(oldExecCount+1)
            newSum2 = oldSum2 + timeExec*timeExec
            newStdDev = abs(newSum2/(oldExecCount+1) - newAvg*newAvg)**0.5
            self.tasksStats[taskKey] = [newAvg, newStdDev, newSum2, oldExecCount+1]

        #print("Receive ADD task", taskKey, timeExec, self.tasksStats[taskKey])
        self.tasksStatsLock.release()


    def _calibrateExecTime(self, runsN = 3):
        timesList = []
        for r in xrange(runsN):
            timeS = time.clock()

            a = 0.
            for i in xrange(10000):
                a = math.sqrt(random.random() / (random.uniform(0,i)+1))

            strT = ""
            for i in xrange(5000):
                strT += str(random.randint(0,9999))

            for i in xrange(500):
                pickStr = pickle.dumps(strT)
                strT = pickle.loads(pickStr)

            timesList.append(time.clock() - timeS)

        return sorted(timesList)[runsN/2]


    def _getLoadTuple(self):
	#if self.dtmExecLock.getLoad() + self.execQueue.getLoad() + self.waitingForRestartQueue.getLoad() == 0.0:
	  #print(">>>>>>>>>>>>>>", self.workerId, self.loadBalancer.ws)
        return (self.dtmExecLock.getLoad(), self.execQueue.getLoad(), self.waitingForRestartQueue.getLoad(), self.waitingThreadsQueue.getLoad())

    def _addWaitingTask(self, taskObj, waitingTIDsList, resultsBuffer):
        self.waitingThreadsLock.acquire()
        self.waitingThreads[taskObj.tid] = (taskObj.waitingCondition, waitingTIDsList, time.clock(), resultsBuffer)
        self.waitingThreadsQueue.put(taskObj)
        self.waitingThreadsLock.release()


    def _returnResult(self, idToReturn, resultInfo):
        """
        Called by the execution threads when they have to return a result
        Should NOT be called explicitly by the user
        """
        if idToReturn == self.workerId:
            self._dispatchResult(resultInfo)
        else:
            self.sendQueue.put((idToReturn, ("Result", self.workerId, (self.loadBalancer.getNodesDict(), self.tasksStats), resultInfo)))

    def _updateStats(self, fromNodeNumber, newDict):
        """
        Called by the control thread to update its dictionnary
        Should NOT be called explicitly by the user
        """

        self.loadBalancer.mergeNodeStatus(newDict[0])

        newTasksStats = newDict[1]
        self.tasksStatsLock.acquire()
        #for key,val in newTasksStats.items():
            #if not key in self.tasksStats:
                #self.tasksStats[key] = val
            #else:
                ##print("Before merge :", self.tasksStats[key])
                #oldAvg, oldStdDev, oldSum2, oldExecCount = self.tasksStats[key]
                #newAvg = (oldAvg*oldExecCount + val[0]*val[3]) / (oldExecCount + val[3])
                #newSum2 = oldSum2 + val[2]
                #try:
                    #newStdDev = (newSum2/(oldExecCount+val[3]) - newAvg*newAvg)**0.5
                #except ValueError:
                    #print(oldExecCount, oldSum2, newSum2, val[3], newAvg)
                    #assert False
                #self.tasksStats[key] = [newAvg, newStdDev, newSum2, oldExecCount+val[3]]
                ##print("After merge :", self.tasksStats[key])

        for key,val in newTasksStats.items():
            if not key in self.tasksStats or val[3] > self.tasksStats[key][3]:
                self.tasksStats[key] = val

        self.tasksStatsLock.release()


    def _dispatchResult(self, result):
        """
        Called by the control thread when a message is received;
        Dispatch it to the task waiting for it.
        Should NOT be called explicitly by the user
        """
        tidParent = result[1]

        self.waitingThreadsLock.acquire()

        self.waitingThreads[tidParent][3][result[2]] = result[4]

        self.waitingThreads[tidParent][1].remove(result[0])
        if len(self.waitingThreads[tidParent][1]) == 0:
            conditionLock = self.waitingThreads[tidParent][0]
            wTask = self.waitingThreadsQueue.getSpecificTask(tidParent)
            assert not wTask is None

            for listAsync in self.asyncWaitingList.values():
                if tidParent in listAsync:
                    conditionLock.acquire()
                    conditionLock.notifyAll()
                    conditionLock.release()
                    self.waitingThreadsLock.release()
                    return

            self.waitingForRestartQueue.put(wTask)

        self.waitingThreadsLock.release()

    def _main(self):
        """
        Main loop of the control thread
        Should NOT be called explicitly by the user
        """
        beg = time.clock()
        realbeg = time.clock()
        p = True
        #f = open("r" + str(self.workerId) + ".csv", "w")
        while True:
            at = time.clock()
            
            #if time.time() - beg > 0.1 and p:
		#time.sleep(3)
            
            #if time.time() - beg > 15:
		#time.sleep(3)	# On attend tous les msgs

            while True:
                try:
                    recvMsg = self.recvQueue.get_nowait()
                    #print("["+str(self.workerId)+"] RECEIVE " + str(recvMsg[MSG_NODES_INFOS]) + " FROM NODE " + str(recvMsg[MSG_SENDER_INFO]))
                    if recvMsg[MSG_COMM_TYPE] == "Exit":
                        self.exitStatus.set()
                        self.exitState = (recvMsg[2], recvMsg[3])
                        break
                    elif recvMsg[MSG_COMM_TYPE] == "Task":
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                        self.execQueue.putList(recvMsg[4])
                        self.loadBalancer.updateSelfStatus(self._getLoadTuple())
                        # recvMsg[5] contient le numero ACK a renvoyer
                        self.sendQueue.put((recvMsg[MSG_SENDER_INFO], ("AckReceptTask", self.workerId, (self.loadBalancer.getNodesDict(), self.tasksStats), recvMsg[5])))
                        #for taskData in recvMsg[4]:
                            #taskData[4].append(self.workerId)
                            #self.execQueue.put(taskData)
                    elif recvMsg[MSG_COMM_TYPE] == "RequestTask":
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                    elif recvMsg[MSG_COMM_TYPE] == "AckReceptTask":
                        self.loadBalancer.acked(recvMsg[MSG_SENDER_INFO], recvMsg[3])
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                    elif recvMsg[MSG_COMM_TYPE] == "Result":
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                        self._dispatchResult(recvMsg[3])
                    else:
                        print("DTM warning : unknown message type ("+str(recvMsg[MSG_COMM_TYPE])+") received will be ignored.")
                except Queue.Empty:
                    break
	    
	    #if time.time() - beg > 3 and p:
		#print("xxxxxxxxxxxxxx ", self.workerId, self.execQueue.getLen())
		#p = False
	    
	    #if time.time() - beg > 18:
		#print("wwwwwwwwwwwwwwwwwwwwwww ", self.workerId, self.execQueue.getLen())
		#break
	    
            if self.exitStatus.is_set():
                break

            currentNodeStatus = self._getLoadTuple()
            #print(self.workerId, currentNodeStatus)
            self.loadBalancer.updateSelfStatus(currentNodeStatus)

            sendUpdateList, sendTasksList = self.loadBalancer.takeDecision()
	    
            self.tasksStatsLock.acquire()
            for sendInfo in sendTasksList:
                #print("["+str(self.workerId)+"] SEND " + str(self.tasksStats) + " TO " + str(sendInfo[0]))
                # sendInfo[2] contient le numero d'ACK a renvoyer
                self.sendQueue.put((sendInfo[0], ("Task", self.workerId, (self.loadBalancer.getNodesDict(), self.tasksStats), len(sendInfo[1]), sendInfo[1], sendInfo[2])))
                #print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$", self.sendQueue.qsize())

            for updateTo in sendUpdateList:
                #print("["+str(self.workerId)+"] SEND " + str(self.tasksStats) + " TO " + str(updateTo))
                self.sendQueue.put((updateTo, ("RequestTask", self.workerId, (self.loadBalancer.getNodesDict(), self.tasksStats), time.time())))
                #print("########$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$", self.sendQueue.qsize())
            self.tasksStatsLock.release()

        #print("STATE WORKER " + str(self.workerId) + "\n" + str(currentNodeStatus))
        ##if time.clock()-at > 0.0005:
        ##print(self.workerId, ">>>>>>>>>>>", time.clock()-at)
	    
	    #if time.clock()-beg > 0.02 and time.clock()-realbeg < 1:
		#f.write(str(time.clock()-realbeg) + "," + str(currentNodeStatus)+"\n")
		#f.flush()
		#beg = time.clock()
	    
            if not self.dtmExecLock.isLocked():
                try:
                    wTask = self.waitingForRestartQueue.getTask()
                    wTask.waitingCondition.acquire()
                    wTask.waitingCondition.notifyAll()
                    wTask.waitingCondition.release()
                    continue
                except Queue.Empty:
                    pass

                try:
                    newTask = self.execQueue.getTask()
                    newThread = DtmThread(tid=newTask[0], returnInfo=(newTask[1],newTask[2],newTask[3]), depth=newTask[6], target=newTask[7], taskCreationTime=newTask[5], args=newTask[8], kwargs=newTask[9], control=self)
                    newThread.start()
                    continue
                except Queue.Empty:
                    pass

            time.sleep(DTM_CONTROL_THREAD_LATENCY)

        if self.commThread.isRootWorker:
            _printDtmMsg("DTM on rank " + str(self.workerId) + " receive an exit signal. Will quit NOW.")
        self._doCleanUp()


    def setOptions(self, *args, **kwargs):
        """
        Set a DTM global option.
        .. warning::
            This function must be called BEFORE ``start()``. It is also the user responsability to ensure that the same option is set on every worker.

        Currently, the supported options are :
            * **communicationManager** : can be *pympi* (default), *mpi4py* (experimental) or *multiprocTCP* (experimental)

        This function can be called more than once.
        """
        assert not self.isStarted, "Fatal error : dtm.setOptions() called after dtm.start()!"
        for opt in kwargs:
            if opt == "communicationManager":
                self.commManagerType = kwargs[opt]


    def start(self, initialTarget, *args, **kwargs):
        """
        Start the execution with the target `initialTarget`.
        Calling this function create and launch the first task on the root worker
        (defined by the communication manager, for instance, with MPI, the root worker is the worker with rank 0.).

        .. warning::
            This function must be called only ONCE, and after the target has been parsed by the Python interpreter.
        """
        self.isStarted = True

        if self.commManagerType == "pympi":
            from commManager import DtmCommThread
        elif self.commManagerType == "mpi4py":
            from commManagerMpi4py import DtmCommThread
        elif self.commManagerType == "multiprocTCP":
            from commManagerTCP import DtmCommThread
        else:
            _printDtmMsg("Warning : '"+str(self.commManagerType)+"' is not a suitable communication manager. Default to pyMPI.")
            from commManager import DtmCommThread

        self.commThread = DtmCommThread(self.recvQueue, self.sendQueue, self.commExitNotification, self.commReadyEvent)

        self.refTime = self._calibrateExecTime()

        self.commThread.start()
        self.commReadyEvent.wait()

        self.poolSize = self.commThread.poolSize
        self.workerId = self.commThread.workerId

        self.idGenerator = DtmTaskIdGenerator(self.workerId)

        self.loadBalancer = DtmLoadBalancer(self.commThread.iterOverIDs(), self.workerId, self.execQueue)

        if self.commThread.isRootWorker:
            _printDtmMsg("DTM started with " + str(self.poolSize) + " workers")
            initTask = (self.idGenerator.tid, None, None, None, [self.workerId], time.clock(), 0, initialTarget, args, kwargs)
            self.execQueue.put(initTask)

        self._main()



    # The following methods are NOT called by the control thread, but by the EXECUTION THREADS
    # All the non-local objects used MUST be thread-safe

    def map(self, function, iterable):
        """
        A parallel equivalent of the `map() <http://docs.python.org/library/functions.html#map>`_ built-in function (it supports only one iterable argument though). It blocks till the result is ready.
        This method chops the iterable into a number of chunks determined by DTM in order to get the most efficient use of the workers.
        """

        listTid = []
        currentId = threading.currentThread().tid

        listResults = [None] * len(iterable)
        listTasks = []

        self.waitingThreadsLock.acquire()

        for index,elem in enumerate(iterable):
            task = (self.idGenerator.tid, self.workerId, currentId, index, [self.workerId], time.clock(), threading.currentThread().depth+1, function, (elem,), {})
            listTid.append(task[0])
            listTasks.append(task)

        self.execQueue.putList(listTasks)

        self.waitingThreadsLock.release()

        self._addWaitingTask(threading.currentThread(), listTid, listResults)
        #self.waitingThreads[currentId] = (conditionObject, listTid, time.clock(), listResults)
        #self.waitingThreadsLock.release()

        time_wait = threading.currentThread().waitForCondition()

        self.waitingThreadsLock.acquire()
        ret = self.waitingThreads[currentId][3]
        del self.waitingThreads[currentId]
        self.waitingThreadsLock.release()

        return ret


    def map_async(self, function, iterable, callback=None):
        """
        A non-blocking variant of the ``DtmControl.map()`` method which returns a result object.
        .. note::
            As on version 0.6, callback is not implemented.
        """

        threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, depth=threading.currentThread().depth, target=function, args=iterable, control=self)
        asyncRequest = DtmAsyncResult(threadAsync, control=self)

        return asyncRequest


    def _apply(self, function, args, kwargs):
        """
        Special function that can be used on boot apply() and apply_async()
        Should not be called directly by the user, as apply() do almost the same job.
        """
        currentId = threading.currentThread().tid

        task = (self.idGenerator.tid, self.workerId, currentId, 0, [self.workerId], time.clock(), threading.currentThread().depth+1, function, args, kwargs)
        self._addWaitingTask(threading.currentThread(), [task[0]], [None])
        self.execQueue.put(task)


        time_wait = threading.currentThread().waitForCondition()

        self.waitingThreadsLock.acquire()
        ret = self.waitingThreads[currentId][3]
        del self.waitingThreads[currentId]
        self.waitingThreadsLock.release()

        return ret[0]

    def apply(self, function, *args, **kwargs):
        """
        Equivalent of the `apply() <http://docs.python.org/library/functions.html#apply>`_ built-in function. It blocks till the result is ready.
        Given this blocks, `apply_async()` is better suited for performing work in parallel.
        Additionally, the passed in function is only executed in one of the workers of the pool.
        """
        return self._apply(function, args, kwargs)

    def apply_async(self, function, *args, **kwargs):
        """
        A non-blocking variant of the apply() method which returns a result object.
        """
        threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, depth=threading.currentThread().depth, target=function, args=args, kwargs=kwargs, control=self, areArgsIterable = False)
        asyncRequest = DtmAsyncResult(threadAsync, control=self)
        return asyncRequest

    def imap(self, function, iterable, chunksize=1):
        """
        An equivalent of `itertools.imap() <http://docs.python.org/library/itertools.html#itertools.imap>`_.

        The chunksize argument can be used to tell DTM how many elements should be computed at the same time.
        For very long iterables using a large value for chunksize can make make the job complete much faster than using the default value of 1.
        """
        currentIndex = 0

        while currentIndex < len(iterable):
            maxIndex = currentIndex+chunksize if currentIndex + chunksize < len(iterable) else len(iterable)
            asyncResults = [None] * (maxIndex - currentIndex)
            for i in xrange(currentIndex, maxIndex):
                asyncResults[i%chunksize] = self.apply_async(function, iterable[i])

            for result in asyncResults:
                ret = result.get()
                yield ret

            currentIndex = maxIndex


    def imap_unordered(self, function, iterable, chunksize=1):
        # Cette implementation a un probleme : contrairement a imap(),
        # on n'attend pas un resultat specifique, mais n'importe lequel
        # Idealement, il faudrait implementer un dtm.waitAny()
        raise NotImplementedError


    def filter(self, function, iterable):
        # Le filtrage s'effectue dans ce thread, mais le calcul est distribue
        results = self.map(function, iterable)
        return [item for result, item in zip(results, iterable) if result]

    def repeat(self, function, howManyTimes, *args, **kwargs):
        # Repete une fonction avec les memes arguments et renvoie une liste contenant les resultats
        # Pas encore implemente
        results = [None] * howManyTimes

        raise NotImplementedError
        return results

    def terminate(self):
        # Termine l'execution
        # Comportement plus ou moins defini avec MPI si appele sur autre chose que le rank 0
        self.exitSetHere = True
        self.exitStatus.set()
        return None


    def waitForAll(self):
        # Met le thread en pause et attend TOUS les resultats asynchrones

        threadId = threading.currentThread().tid

        self.asyncWaitingListLock.acquire()
        if len(self.asyncWaitingList.get(threadId,[])) == 0:
            # Si on a aucun resultat asyncrhone en attente
            self.asyncWaitingListLock.release()
            return None
        else:
            for index in xrange(len(self.asyncWaitingList[threadId])):
                self.asyncWaitingList[threadId][index][1] = True
            self.asyncWaitingListLock.release()
            threading.currentThread().waitForCondition()
        return None

    def testAllAsync(self):
        # Teste si tous les taches asynchrones sont terminees
        self.asyncWaitingListLock.acquire()
        retValue = (len(self.asyncWaitingList.get(threading.currentThread().tid,[])) == 0)
        self.asyncWaitingListLock.release()
        return retValue


    def getWorkerId(self):
        # With MPI, return the slot number
        return self.workerId




class DtmThread(threading.Thread):
    """
    Les threads d'execution sont la base de DTM
    Leur particularite principale est de posseder un lock conditionnel unique
    qui permet d'arreter/repartir le thread lors des appels a DTM
    """
    def __init__(self, group=None, target=None, name=None, control=None, returnInfo = None, depth = 0, tid=None, taskCreationTime = time.clock(), args=(), kwargs={}):
        threading.Thread.__init__(self)

        self.tid = tid
        self.t = target
        self.control = control
        self.returnInfo = returnInfo
        self.depth = depth
        self.waitingCondition = threading.Condition()
        self.argsL = args
        self.kwargsL = kwargs
        self.timeCreation = taskCreationTime
        self.timeExec = 0
        self.timeBegin = 0
        if returnInfo[0] is None:
            self.isRootTask = True
        else:
            self.isRootTask = False

    def run(self):
        # On s'assure qu'aucun autre thread ne s'execute
        self.control.dtmExecLock.acquire()
        
        #print("START EXECUTION OF "+str(self.tid)+"ON " + str(self.control.workerId))

        self.timeBegin = time.clock()
        returnedR = self.t(*self.argsL, **self.kwargsL)
        self.timeExec += time.clock() - self.timeBegin

        try:
            self.control._addTaskStat(self.t.__name__, self.timeExec)
        except AttributeError:
            self.control._addTaskStat(str(self.t), self.timeExec)

        if self.isRootTask:
            # Si la tache racine est terminee alors on quitte
            self.control.exitSetHere = True
            self.control.exitStatus.set()
        else:
            # Sinon on retourne le resultat
            resultTuple = (self.tid, self.returnInfo[1], self.returnInfo[2], self.timeExec, returnedR)
            self.control._returnResult(self.returnInfo[0], resultTuple)

        self.control.dtmExecLock.release()


    def waitForCondition(self):
        # Libere le lock d'execution et attend que la condition soit remplie pour continuer
        self.waitingCondition.acquire()

        beginTimeWait = time.clock()
        self.timeExec += beginTimeWait - self.timeBegin
        self.control.dtmExecLock.release()

        self.waitingCondition.wait()
        self.waitingCondition.release()

        self.control.dtmExecLock.acquire()
        self.timeBegin = time.clock()
        return time.clock() - beginTimeWait


class DtmAsyncWaitingThread(threading.Thread):
    """
    Cette classe est semblable a DtmThread; elle sert de thread d'attente aux taches asynchrones
    (car le fonctionnement de DTM suppose que tout resultat est attendu par un thread et son lock conditionnel)
    Par ailleurs, elle notifie un objet special lorsque son resultat est arrive
    """
    def __init__(self, tid = None, depth = 0, target = None, args = (), kwargs = {}, areArgsIterable = True, taskCreationTime = time.clock(), control = None, returnToObj = None):
        threading.Thread.__init__(self)
        self.tid = tid
        self.task_target = target
        self.depth = depth
        self.args = args
        self.kwargs = kwargs
        self.iterable = areArgsIterable
        self.timeCreation = taskCreationTime
        self.control = control
        self.waitingCondition = threading.Condition()
        self.returnTo = returnToObj         # Cet objet doit avoir une methode _giveResult(resultat)
        self.t = None   # Son target n'existe pas
        self.timeExec = 0

    def setObjToReturnTo(self, obj):
        self.returnTo = obj

    def run(self):
        if self.iterable:
            result = self.control.map(self.task_target, self.args)
        else:
            result = self.control._apply(self.task_target, self.args, self.kwargs)

        self.returnTo._giveResult(result)
        return

    def waitForCondition(self):
        self.waitingCondition.acquire()
        self.waitingCondition.wait()
        self.waitingCondition.release()


class DtmAsyncResult(object):
    """
    The class of the result returned by **DtmControl.map_async()** and **DtmControl.apply_async()**.
    """
    def __init__(self, asyncThread, control):
        self.rThread = asyncThread
        self.dtmInterface = control
        self.resultReturned = False
        self.resultVal = None
        self.rThread.setObjToReturnTo(self)
        self.returnThread = threading.currentThread()

        self.dtmInterface.asyncWaitingListLock.acquire()
        self.dtmInterface.asyncWaitingList.setdefault(self.returnThread.tid, []).append([self.rThread.tid, False])
        self.dtmInterface.asyncWaitingListLock.release()

        self.rThread.start()

    def _giveResult(self, result):
        # This method will be used by the async thread to return result
        self.resultReturned = True
        self.resultVal = result
        self.dtmInterface.asyncWaitingListLock.acquire()
        blockingAsyncTasksBefore = len([aTask for aTask in self.dtmInterface.asyncWaitingList[self.returnThread.tid] if aTask[1]])
        for index,aTask in enumerate(self.dtmInterface.asyncWaitingList[self.returnThread.tid]):
            if aTask[0] == self.rThread.tid:
                del self.dtmInterface.asyncWaitingList[self.returnThread.tid][index]

        if blockingAsyncTasksBefore > 0 and len([aTask for aTask in self.dtmInterface.asyncWaitingList[self.returnThread.tid] if aTask[1]]) == 0:
            # Toutes les taches asynchrones bloquantes sont terminees
            # On est pret a repartir
            self.dtmInterface.waitingForRestartQueue.put(self.returnThread)
        self.dtmInterface.asyncWaitingListLock.release()


    def get(self):
        """
        Return the result when it arrives.
        .. note::
            This is a blocking call : caller will wait in this function until the result is ready.
            To check for the avaibility of the result, use ready()
        """
        if self.ready():
            return self.resultVal
        self.wait()

        return self.resultVal

    def wait(self):
        """
        Wait until the result is available
        """
        if self.ready():
            return

        self.dtmInterface.asyncWaitingListLock.acquire()
        # On indique au thread de controle que l'on wait sur cette tache
        for index,aTask in enumerate(self.dtmInterface.asyncWaitingList[self.returnThread.tid]):
            if aTask[0] == self.rThread.tid:
                self.dtmInterface.asyncWaitingList[self.returnThread.tid][index][1] = True
                break
        self.dtmInterface.asyncWaitingListLock.release()
        threading.currentThread().waitForCondition()


    def ready(self):
        """
        Return whether the asynchronous task has completed.
        """
        return not self.rThread.isAlive()

    def successful(self):
        """
        Return whether the task completed without error. Will raise AssertionError if the result is not ready.
        """
        if self.rThread.isAlive():
            raise AssertionError("Call DtmAsyncResult.successful() before the results were ready!")
        return self.resultReturned


dtm = DtmControl()