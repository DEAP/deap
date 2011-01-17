import threading
import time
import math
import random
import Queue
import copy
import pickle
import logging
import sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
_logger = logging.getLogger("dtm.control")

# Constantes
DTM_CONTROL_THREAD_LATENCY = 0.05

MSG_COMM_TYPE = 0
MSG_SENDER_INFO = 1
MSG_NODES_INFOS = 2

try:
     # math.erf() is implemented only since Python 2.7
    from math import erf
except ImportError:
    def erf(x):
        # See http://stackoverflow.com/questions/457408/
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

        if areaPart1 == areaPart2:
            # Tellement loin de la moyenne que erf(alreadyDone - moyenne) = 1
            previsionPoint = alreadyDone + 0.5      # On "suppose" qu'il reste 0.5 secondes
        else:
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
            timeDone = self.eCurrent.timeExec
            if hasattr(self.eCurrent.t, 'dtmExpectedDuration'):
                if isinstance(self.eCurrent.t.dtmExpectedDuration, tuple):
                    return self._execTimeRemaining(self.eCurrent.t.dtmExpectedDuration[0], self.eCurrent.t.dtmExpectedDuration[1], timeDone)
                else:
                    if self.eCurrent.t.dtmExpectedDuration-timeDone <= 0:
                        return 1.
                    else:
                        return self.eCurrent.t.dtmExpectedDuration-timeDone
            elif hasattr(self.eCurrent.t, 'dtmDurationMetric'):
                self.eCurrent.t.dtmExpectedDuration = self.eCurrent.t.dtmDurationMetric(*self.eCurrent.argsL, **self.eCurrent.kwargsL)
                if isinstance(self.eCurrent.t.dtmExpectedDuration, tuple):
                    return self._execTimeRemaining(self.eCurrent.t.dtmExpectedDuration[0], self.eCurrent.t.dtmExpectedDuration[1], timeDone)
                else:
                    if self.eCurrent.t.dtmExpectedDuration-timeDone <= 0:
                        return 1.
                    else:
                        return self.eCurrent.t.dtmExpectedDuration-timeDone
            else:
                try:
                    self.tStatsLock.acquire()
                    tInfo = self.tStats.get(self.eCurrent.t, [1,1,0,0])
                    val = self._execTimeRemaining(tInfo[0], tInfo[1], timeDone)
                    self.tStatsLock.release()
                    return val
                except AttributeError:
                    self.tStatsLock.release()
                    return 0.
        except AttributeError:
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
        # Attention, cette fonction peut modifier les taches
        # qui lui sont passees (elle peut ajouter ou enlever
        # des attributs au target)
        if isinstance(task, tuple):
            target = task[7]
            timeDone = 0.
        else:
            target = task.t
            timeDone = task.timeExec

        
        if hasattr(target, 'dtmExpectedDuration'):
            if isinstance(target.dtmExpectedDuration, tuple):
                return self._execTimeRemaining(target.dtmExpectedDuration[0], target.dtmExpectedDuration[1], timeDone)
            else:
                if target.dtmExpectedDuration-timeDone <= 0:
                    return 1.
                else:
                    return target.dtmExpectedDuration-timeDone
        elif hasattr(target, 'dtmDurationMetric'):
            if isinstance(task, tuple):
                argsT, kwargsT = task[8], task[9]
            else:
                argsT, kwargsT = task.argsL, task.kwargsL

            target.dtmExpectedDuration = target.dtmDurationMetric(*argsT, **kwargsT)
            if isinstance(target.dtmExpectedDuration, tuple):
                return self._execTimeRemaining(target.dtmExpectedDuration[0], target.dtmExpectedDuration[1], timeDone)
            else:
                if target.dtmExpectedDuration-timeDone <= 0:
                    return 1.
                else:
                    return target.dtmExpectedDuration-timeDone
        else:    
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

        if areaPart1 == areaPart2:
            # Tellement loin de la moyenne que erf(alreadyDone - moyenne) = 1
            previsionPoint = alreadyDone + 0.5      # On "suppose" qu'il reste 0.5 secondes
        else:
            previsionPoint = (massCenterPart2 - massCenterPart1)/(areaPart2 - areaPart1)

        return previsionPoint - alreadyDone

    def put(self, taskObject):
        self.putList([taskObject])

    def putList(self, tasksList):
        self._actionLock.acquire()

        for taskObject in tasksList:
            if isinstance(taskObject, tuple):
                self._tQueue.put((taskObject[5], taskObject))
                self._tDict[taskObject[0]] = taskObject
            else:
                self._tQueue.put((taskObject.timeCreation, taskObject))
                self._tDict[taskObject.tid] = taskObject
        
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
        #print("LOAD", tmpLoad)
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
        #
        # Pour contourner le bug du demarrage avec peu de jobs tres longues
        # Pas sur que ce soit la meilleure solution sur le long terme mais bon...
        if len(returnList) == 0 and maxDiff == -1 and len(self._tDict) > 1:
            # Si on a aucune tache, on en ajoute une au hasard
            it = filter(lambda x: self._getTimeInfoAbout(x[1]) != 0, self._tDict.items())
            if len(it) != 0:
                returnList.append(it[0][0])
                totalTime += self._getTimeInfoAbout(it[0][1])
        self._actionLock.release()
        return returnList, totalTime



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

        self.globalTasksStats = {}  # Dictionnaire de dictionnaire (premiere cle : wId, deuxieme cle : identifiant de tache)
        self.globalTasksStatsLock = threading.Lock()

        # Lock d'execution global qui assure qu'un seul thread a la fois
        # essaie de s'executer
        # Il permet aussi de savoir au thread de controle si on execute encore quelque chose
        self.dtmExecLock = DtmExecInfo(self.tasksStats, self.tasksStatsLock)

        self.waitingThreadsQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)
        self.waitingThreads = {}
        self.waitingThreadsLock = threading.Lock()

        self.asyncWaitingList = {}
        self.asyncWaitingListLock = threading.Lock()

        self.launchTaskLock = threading.Lock()

        self.waitingForRestartQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)
        self.execQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)

        self.recvQueue = Queue.Queue()
        self.sendQueue = Queue.Queue()

        self.exitStatus = threading.Event()

        self.commExitNotification = threading.Event()

        self.commReadyEvent = threading.Event()

        self.exitState = (None, None)
        self.exitSetHere = False

        self.commManagerType = "mpi4py"
        self.loadBalancerType = "PDB"
        self.printExecSummary = True
        
        self.isStarted = False

        self.refTime = 1.

        self.loadBalancer = None

        self.nbrTasksDone = 0

        self.lastRetValue = None
        
        self.dtmRandom = random.Random()

        """
        dtmExpectedDuration
        dtmDurationMetric
        """



    def _doCleanUp(self):
        """
        Clean up function, called at this end of the execution.
        Should NOT be called by the user.
        """

        if self.printExecSummary:
             _logger.info("[%s] did %i tasks", str(self.workerId), self.nbrTasksDone)

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
            _logger.warning("[%s] There's more than 1 active thread (%i) at the exit.", str(self.workerId), threading.activeCount())

        if self.commThread.isRootWorker:
            if self.printExecSummary:
                msgT = " Tasks execution times summary :\n"
                for target,times in self.tasksStats.items():
                    msgT += "\t" + str(target) + " : Avg=" + str(times[0]*self.refTime) + ", StdDev=" + str(times[1]*self.refTime) + "\n\n"
                _logger.info(msgT)

            _logger.info("DTM execution ended (no more tasks)")
            _logger.info("Total execution time for root worker : %s", str(time.clock() - self.sTime))

        return self.lastRetValue


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

        self.tasksStatsLock.release()


    def _calibrateExecTime(self, runsN = 3):
        """
        Small calibration test, run at startup
        Should not be called by user
        """
        timesList = []
        for r in xrange(runsN):
            timeS = time.clock()

            a = 0.
            for i in xrange(10000):
                a = math.sqrt(self.dtmRandom.random() / (self.dtmRandom.uniform(0,i)+1))

            strT = ""
            for i in xrange(5000):
                strT += str(self.dtmRandom.randint(0,9999))

            for i in xrange(500):
                pickStr = pickle.dumps(strT)
                strT = pickle.loads(pickStr)

            timesList.append(time.clock() - timeS)

        return sorted(timesList)[runsN/2]


    def _getLoadTuple(self):
        return (self.dtmExecLock.getLoad(), self.execQueue.getLoad(), self.waitingForRestartQueue.getLoad(), self.waitingThreadsQueue.getLoad())


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
            while wTask is None:
                # Peut se produire si le thread parent ne s'est pas encore mis en sleep
                time.sleep(0.001)
                wTask = self.waitingThreadsQueue.getSpecificTask(tidParent)
            #assert not wTask is None

            self.asyncWaitingListLock.acquire()
            for listAsync in self.asyncWaitingList.values():
                # Les threads representant les taches asynchrones
                # peuvent recommencer immediatement
                for taskAsync in listAsync:
                    if taskAsync[0] == tidParent:
                        conditionLock.acquire()
                        conditionLock.notifyAll()
                        conditionLock.release()
                        self.asyncWaitingListLock.release()
                        self.waitingThreadsLock.release()
                        return

            self.asyncWaitingListLock.release()
            self.waitingForRestartQueue.put(wTask)

        self.waitingThreadsLock.release()
        

    def _startNewTask(self):
        """
        Start a new task (if there's one available)
        Return True if so
        Should NOT be called explicitly by the user
        """
        taskLauched = False
        self.launchTaskLock.acquire()
        if not self.dtmExecLock.isLocked():
            try:
                wTask = self.waitingForRestartQueue.getTask()
                wTask.waitingCondition.acquire()
                wTask.waitingCondition.notifyAll()
                wTask.waitingCondition.release()
                taskLauched = True
            except Queue.Empty:
                pass
            except RuntimeError:
                # Il se peut que le thread n'aie pas encore eu le temps de se mettre en wait
                wTask = self.waitingForRestartQueue.getTask()
                wTask.waitingCondition.acquire()
                wTask.waitingCondition.notifyAll()
                wTask.waitingCondition.release()
                taskLauched = True

            if not taskLauched:
                try:
                    newTask = self.execQueue.getTask()
                    newThread = DtmThread(tid=newTask[0], returnInfo=(newTask[1],newTask[2],newTask[3]), depth=newTask[6], target=newTask[7], taskCreationTime=newTask[5], args=newTask[8], kwargs=newTask[9], control=self)
                    newThread.start()
                    self.nbrTasksDone += 1
                    taskLauched = True
                except Queue.Empty:
                    pass
            
        self.launchTaskLock.release()
        return taskLauched
    
    def _main(self):
        """
        Main loop of the control thread
        Should NOT be called explicitly by the user
        """
        dataLoadB = ""
        timeBegin = time.time()
        dataStep = 30
        stepCount = 0

        while True:
            stepCount += 1
            while True:
                try:
                    recvMsg = self.recvQueue.get_nowait()
                    if recvMsg[MSG_COMM_TYPE] == "Exit":
                        self.exitStatus.set()
                        self.exitState = (recvMsg[2], recvMsg[3])
                        break
                    elif recvMsg[MSG_COMM_TYPE] == "Task":
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                        self.execQueue.putList(recvMsg[4])
                        self.loadBalancer.updateSelfStatus(self._getLoadTuple())
                        self.loadBalancer.notifyTaskReceivedFrom(recvMsg[MSG_SENDER_INFO])
                        self.sendQueue.put((recvMsg[MSG_SENDER_INFO], ("AckReceptTask", self.workerId, (self.loadBalancer.getNodesDict(), self.tasksStats), recvMsg[5])))
                    elif recvMsg[MSG_COMM_TYPE] == "RequestTask":
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                    elif recvMsg[MSG_COMM_TYPE] == "AckReceptTask":
                        self.loadBalancer.acked(recvMsg[MSG_SENDER_INFO], recvMsg[3])
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                    elif recvMsg[MSG_COMM_TYPE] == "Result":
                        self._updateStats(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                        self._dispatchResult(recvMsg[3])
                    else:
                        _logger.warning("[%s] Unknown message type '%s' received will be ignored.", str(self.workerId), recvMsg[MSG_COMM_TYPE])
                except Queue.Empty:
                    break

	    
            if self.exitStatus.is_set():
                break
	    

            currentNodeStatus = self._getLoadTuple()
            self.loadBalancer.updateSelfStatus(currentNodeStatus)

            sendUpdateList, sendTasksList = self.loadBalancer.takeDecision()
            self.tasksStatsLock.acquire()
            for sendInfo in sendTasksList:
                self.sendQueue.put((sendInfo[0], ("Task", self.workerId, (self.loadBalancer.getNodesDict(), self.tasksStats), len(sendInfo[1]), sendInfo[1], sendInfo[2])))

            for updateTo in sendUpdateList:
                self.sendQueue.put((updateTo, ("RequestTask", self.workerId, (self.loadBalancer.getNodesDict(), self.tasksStats), time.time())))
            self.tasksStatsLock.release()

            #if stepCount >= dataStep:
                #dataLoadB += str(time.time()-timeBegin) + "," + str(self.execQueue.getLen()+\
                #self.waitingForRestartQueue.getLen()+\
                #self.waitingThreadsQueue.getLen()+int(self.dtmExecLock.isLocked())) + "\n"
                #stepCount = 0
                #print("//////////////////////", self.workerId, self.execQueue.getLen(), self.waitingForRestartQueue.getLen(), self.waitingThreadsQueue.getLen())
            
            if not self._startNewTask():
                time.sleep(DTM_CONTROL_THREAD_LATENCY)

        #time.sleep(self.workerId/4.)
        #print("DATA WORKER " + str(self.workerId) + "\n" + dataLoadB + "\n\n\n")
        return self._doCleanUp()


    def setOptions(self, *args, **kwargs):
        """
        Set a DTM global option.
        .. warning::
            This function must be called BEFORE ``start()``. It is also the user responsability to ensure that the same option is set on every worker.

        Currently, the supported options are :
            * **communicationManager** : can be *pympi* (experimental), *mpi4py* (default) or *multiprocTCP* (experimental)

        This function can be called more than once.
        """
        if self.isStarted:
            if self.commThread.isRootWorker:
                _logger.warning("dtm.setOptions() was called after dtm.start(); options will not be considered")
            return
            
        for opt in kwargs:
            if opt == "communicationManager":
                self.commManagerType = kwargs[opt]
            elif opt == "loadBalancer":
                self.loadBalancerType = kwargs[opt]
            elif opt == "printSummary":
                self.printExecSummary = kwargs[opt]
            elif self.commThread.isRootWorker:
                _logger.warning("Unknown option '%s'", opt)


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
            _logger.warning("Warning : %s is not a suitable communication manager. Default to mpi4py.", self.commManagerType)
            from commManagerMpi4py import DtmCommThread

        if self.loadBalancerType == "PDB":
            from loadBalancerPDB import DtmLoadBalancer
        else:
            _logger.warning("Warning : %s is not a suitable load balancer. Default to PDB.", self.loadBalancerType)
            from loadBalancerPDB import DtmLoadBalancer

        self.commThread = DtmCommThread(self.recvQueue, self.sendQueue, self.commExitNotification, self.commReadyEvent)

        self.refTime = self._calibrateExecTime()

        self.commThread.start()
        self.commReadyEvent.wait()

        self.poolSize = self.commThread.poolSize
        self.workerId = self.commThread.workerId

        self.idGenerator = DtmTaskIdGenerator(self.workerId)

        self.loadBalancer = DtmLoadBalancer(self.commThread.iterOverIDs(), self.workerId, self.execQueue, self.dtmRandom)

        if self.commThread.isRootWorker:
            _logger.info("DTM started with %i workers", self.poolSize)
            _logger.info("DTM load balancer is %s, and communication manager is %s", self.loadBalancerType, self.commManagerType)
            initTask = (self.idGenerator.tid, None, None, None, [self.workerId], time.time(), 0, initialTarget, args, kwargs)
            self.execQueue.put(initTask)

        return self._main()



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

        for index,elem in enumerate(iterable):
            task = (self.idGenerator.tid, self.workerId, currentId, index, [self.workerId], time.time(), threading.currentThread().depth+1, function, (elem,), {})
            listTid.append(task[0])
            listTasks.append(task)
            
        self.waitingThreadsLock.acquire()
        self.waitingThreads[currentId] = (threading.currentThread().waitingCondition, listTid, time.clock(), listResults)        
        self.waitingThreadsLock.release()
        
        self.execQueue.putList(listTasks)

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
            As on version 0.1, callback is not implemented.
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
        
        task = (self.idGenerator.tid, self.workerId, currentId, 0, [self.workerId], time.time(), threading.currentThread().depth+1, function, args, kwargs)
        self.waitingThreadsLock.acquire()       
        self.waitingThreads[currentId] = (threading.currentThread().waitingCondition, [task[0]], time.clock(), [None])        
        self.waitingThreadsLock.release()
        
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
        listResults = [None] * howManyTimes

        listTasks = []
        listTid = []
        currentId = threading.currentThread().tid

        
        for i in xrange(howManyTimes):
            task = (self.idGenerator.tid, self.workerId, currentId, i, [self.workerId], time.time(), threading.currentThread().depth+1, function, args, kwargs)
            listTid.append(task[0])
            listTasks.append(task)
            
        self.waitingThreadsLock.acquire()
        self.waitingThreads[currentId] = (threading.currentThread().waitingCondition, listTid, time.clock(), listResults)
        self.waitingThreadsLock.release()

        self.execQueue.putList(listTasks)

        time_wait = threading.currentThread().waitForCondition()

        self.waitingThreadsLock.acquire()
        ret = self.waitingThreads[currentId][3]
        del self.waitingThreads[currentId]
        self.waitingThreadsLock.release()

        return ret

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

        self.timeBegin = time.clock()
        returnedR = self.t(*self.argsL, **self.kwargsL)
        self.timeExec += time.clock() - self.timeBegin

        try:
            self.control._addTaskStat(self.t.__name__, self.timeExec)
        except AttributeError:
            self.control._addTaskStat(str(self.t), self.timeExec)

        self.control.dtmExecLock.release()
        
        if self.isRootTask:
            # Si la tache racine est terminee alors on quitte
            self.control.lastRetValue = returnedR
            self.control.exitSetHere = True
            self.control.exitStatus.set()
        else:
            # Sinon on retourne le resultat
            resultTuple = (self.tid, self.returnInfo[1], self.returnInfo[2], self.timeExec, returnedR)
            self.control._returnResult(self.returnInfo[0], resultTuple)

        # On tente de lancer tout de suite une nouvelle tache
        self.control._startNewTask()
    

    def waitForCondition(self):
        # Libere le lock d'execution et attend que la condition soit remplie pour continuer
        
        self.waitingCondition.acquire()

        beginTimeWait = time.clock()
        self.timeExec += beginTimeWait - self.timeBegin
        self.control.dtmExecLock.release()

        self.control._startNewTask()

        self.control.waitingThreadsQueue.put(threading.currentThread())
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
        self.control.waitingThreadsQueue.put(threading.currentThread())
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
        self.resultVal = result
        self.dtmInterface.asyncWaitingListLock.acquire()
        blockingAsyncTasksBefore = len([aTask for aTask in self.dtmInterface.asyncWaitingList[self.returnThread.tid] if aTask[1]])

        self.dtmInterface.asyncWaitingList[self.returnThread.tid] = filter(lambda aTask: not aTask[0] == self.rThread.tid,
            self.dtmInterface.asyncWaitingList[self.returnThread.tid])

        if blockingAsyncTasksBefore > 0 and len([aTask for aTask in self.dtmInterface.asyncWaitingList[self.returnThread.tid] if aTask[1]]) == 0:
            # Toutes les taches asynchrones bloquantes sont terminees
            # On est pret a repartir
            wTask = self.dtmInterface.waitingThreadsQueue.getSpecificTask(self.returnThread.tid)
            while wTask is None:
                # Peut se produire si le thread parent ne s'est pas encore mis en sleep
                time.sleep(0.001)
                wTask = self.dtmInterface.waitingThreadsQueue.getSpecificTask(self.returnThread.tid)
            self.dtmInterface.waitingForRestartQueue.put(self.returnThread)
        self.dtmInterface.asyncWaitingListLock.release()

        self.resultReturned = True


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
       
        # On indique au thread de controle que l'on wait sur cette tache
        taskBlockAdded = False
        while not taskBlockAdded:
            self.dtmInterface.asyncWaitingListLock.acquire()
            for index,aTask in enumerate(self.dtmInterface.asyncWaitingList[self.returnThread.tid]):
                if aTask[0] == self.rThread.tid:
                    self.dtmInterface.asyncWaitingList[self.returnThread.tid][index][1] = True
                    #print(self.dtmInterface.asyncWaitingList[self.returnThread.tid])
                    taskBlockAdded = True
                    break
            self.dtmInterface.asyncWaitingListLock.release()
            
            if not taskBlockAdded:
                # Tricky : il se peut que la tache soit retourne, mais le thread pas encore termine
                # (il est dans _giveResult)
                if self.ready():
                    return
                time.sleep(0.1)
            
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
