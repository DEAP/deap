import threading
import time
import math
import random
try:
    import Queue
except ImportError:
    import queue as Queue
import copy
import pickle
import logging
import sys

from dtmTypes import *

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
_logger = logging.getLogger("dtm.control")

# Constantes
DTM_CONTROL_THREAD_LATENCY = 0.05

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


    def acquire(self, forTask, blocking=True):
        if self.eLock.acquire(blocking):
            self.eCurrent = forTask
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
            tInfo = self.tStats.get(self.eCurrent.target, DtmStatsContainer({'rAvg':1., 'rStdDev':1., 'rSquareSum':0., 'execCount':0}))
            val = self._execTimeRemaining(tInfo.rAvg, tInfo.rStdDev, self.eCurrent.threadObject.timeExec)
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
        if task.threadObject is None:
            timeDone = 0.
        else:
            timeDone = task.threadObject.timeExec

        self.tStatsLock.acquire()
        tInfo = self.tStats.get(task.target, DtmStatsContainer({'rAvg':1., 'rStdDev':1., 'rSquareSum':0., 'execCount':0}))
        self.tStatsLock.release()

        return self._execTimeRemaining(tInfo.rAvg, tInfo.rStdDev, timeDone)

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
        self.putList((taskObject,))

    def putList(self, tasksList):
        self._actionLock.acquire()

        for taskObject in tasksList:
            self._tDict[taskObject.tid] = taskObject
            self._tQueue.put((taskObject.creationTime, taskObject))
        
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

            if taskObject.tid in self._tDict:
                del self._tDict[taskObject.tid]
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
        #
        # Pour contourner le bug du demarrage avec peu de jobs tres longues
        # Pas sur que ce soit la meilleure solution sur le long terme mais bon...
        if len(returnList) == 0 and maxDiff == -1 and len(self._tDict) > 1:
            # Si on a aucune tache, on en ajoute une au hasard
            it = list(filter(lambda x: self._getTimeInfoAbout(x[1]) != 0, self._tDict.items()))
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
        
        # Key : Target, Value : DtmStatsContainer
        self.tasksStats = {}
        self.tasksStatsLock = threading.Lock()

        # Lock d'execution global qui assure qu'un seul thread a la fois
        # essaie de s'executer
        # Il permet aussi de savoir au thread de controle si on execute encore quelque chose
        self.dtmExecLock = DtmExecInfo(self.tasksStats, self.tasksStatsLock)

        self.waitingThreadsQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)
        
        # Key : task ID, Value : DtmWaitInfoContainer
        self.waitingThreads = {}
        self.waitingThreadsLock = threading.Lock()


        self.launchTaskLock = threading.Lock()

        self.waitingForRestartQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)
        self.execQueue = DtmTaskQueue(self.tasksStats, self.tasksStatsLock)

        self.recvQueue = Queue.Queue()      # Contains DtmMessageContainer
        self.sendQueue = Queue.Queue()      # Contains DtmMessageContainer

        self.exitStatus = threading.Event()
        self.commExitNotification = threading.Event()
        self.commReadyEvent = threading.Event()

        self.exitState = (None, None)
        self.exitSetHere = False
        
        # Will stop the main thread until an event occurs
        self.runningFlag = threading.Event()
        self.runningFlag.set()

        self.commManagerType = "commManagerMpi4py"
        self.loadBalancerType = "loadBalancerPDB"
        self.printExecSummary = True
        
        self.isStarted = False

        self.refTime = 1.

        self.loadBalancer = None

        self.lastRetValue = None
        
        self.dtmRandom = random.Random()



    def _doCleanUp(self):
        """
        Clean up function, called at this end of the execution.
        Should NOT be called by the user.
        """

        #if self.printExecSummary:
             #_logger.info("[%s] did %i tasks", str(self.workerId), self._DEBUG_COUNT_EXEC_TASKS)

        if self.exitSetHere:
            for n in self.commThread.iterOverIDs():
                if n == self.workerId:
                    continue
                self.sendQueue.put(DtmMessageContainer({'msgType' : DTM_MSG_EXIT,
                                    'senderWid' : self.workerId,
                                    'receiverWid' : n,
                                    'loadsDict' : None,
                                    'targetsStats' : None,
                                    'prepTime' : time.time(),
                                    'sendTime' : 0,
                                    'ackNbr' : -1,
                                    'msg' : (0, "Exit with success")}))

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
                    msgT += "\t" + str(target) + " : Avg=" + str(times.rAvg*self.refTime) + ", StdDev=" + str(times.rStdDev*self.refTime) + "\n\n"
                _logger.info(msgT)

            _logger.info("DTM execution ended (no more tasks)")
            _logger.info("Total execution time : %s", str(time.clock() - self.sTime))
            
        if self.exitSetHere:
            if self.lastRetValue[0]:
                return self.lastRetValue[1]
            else:
                raise self.lastRetValue[1]


    def _addTaskStat(self, taskKey, timeExec):
        # On exprime le temps d'execution d'une tache en reference au temps de calibration
        comparableLoad = timeExec / self.refTime
        # On ne conserve pas tous les temps d'execution
        # La moyenne et l'ecart type sont mis a jour en temps reel
        
        self.tasksStatsLock.acquire()
        if not taskKey in self.tasksStats:
            self.tasksStats[taskKey] = DtmStatsContainer({'rAvg' : timeExec,
                                                'rStdDev' : 0.,
                                                'rSquareSum' : timeExec*timeExec,
                                                'execCount' : 1})
        else:
            oldAvg = self.tasksStats[taskKey].rAvg
            oldStdDev = self.tasksStats[taskKey].rStdDev
            oldSum2 = self.tasksStats[taskKey].rSquareSum
            oldExecCount = self.tasksStats[taskKey].execCount

            self.tasksStats[taskKey].rAvg = (timeExec + oldAvg*oldExecCount)/(oldExecCount+1)
            self.tasksStats[taskKey].rSquareSum = oldSum2 + timeExec*timeExec
            self.tasksStats[taskKey].rStdDev = abs(self.tasksStats[taskKey].rSquareSum/(oldExecCount+1) - self.tasksStats[taskKey].rAvg**2)**0.5
            self.tasksStats[taskKey].execCount = oldExecCount+1

        self.tasksStatsLock.release()


    def _calibrateExecTime(self, runsN = 3):
        """
        Small calibration test, run at startup
        Should not be called by user
        """
        timesList = []
        for r in range(runsN):
            timeS = time.clock()

            a = 0.
            for i in range(10000):
                a = math.sqrt(self.dtmRandom.random() / (self.dtmRandom.uniform(0,i)+1))

            strT = ""
            for i in range(5000):
                strT += str(self.dtmRandom.randint(0,9999))

            for i in range(500):
                pickStr = pickle.dumps(strT)
                strT = pickle.loads(pickStr)

            timesList.append(time.clock() - timeS)

        return sorted(timesList)[int(runsN/2)]


    def _getLoadTuple(self):
        return (self.dtmExecLock.getLoad(), self.execQueue.getLoad(), self.waitingForRestartQueue.getLoad(), self.waitingThreadsQueue.getLoad())


    def _returnResult(self, idToReturn, resultInfo):
        """
        Called by the execution threads when they have to return a result
        Should NOT be called explicitly by the user
        """
        if idToReturn == self.workerId:
            self._dispatchResults((resultInfo,))
        else:
            self.sendQueue.put(DtmMessageContainer({'msgType' : DTM_MSG_RESULT,
                                            'senderWid' : self.workerId,
                                            'receiverWid' : idToReturn,
                                            'loadsDict' : self.loadBalancer.getNodesDict(),
                                            'targetsStats' : self.tasksStats,
                                            'prepTime' : time.time(),
                                            'sendTime' : 0,
                                            'ackNbr' : -1,
                                            'msg' : (resultInfo,)}))

    def _updateStats(self, msg):
        """
        Called by the control thread to update its dictionnary
        Should NOT be called explicitly by the user
        """
        self.loadBalancer.mergeNodeStatus(msg.loadsDict)

        self.tasksStatsLock.acquire()

        for key,val in msg.targetsStats.items():
            if not key in self.tasksStats or val.execCount > self.tasksStats[key].execCount:
                self.tasksStats[key] = val

        self.tasksStatsLock.release()


    def _dispatchResults(self, resultsList):
        """
        Called by the control thread when a message is received;
        Dispatch it to the task waiting for it.
        Should NOT be called explicitly by the user
        """
        for result in resultsList:
            self.waitingThreadsLock.acquire()
            
            # On ne sait pas directement de quelle tache ce resultat provient
            # Mais on sait qu'il est dans :
            foundKey = None
            for taskKey in self.waitingThreads[result.parentTid].rWaitingDict:
                try:
                    self.waitingThreads[result.parentTid].rWaitingDict[taskKey].tids.remove(result.tid)
                except ValueError:
                    # Le ID n'est pas dans cette liste
                    continue
                
                foundKey = taskKey
                if isinstance(self.waitingThreads[result.parentTid].rWaitingDict[taskKey].result, list):
                    # Si une exception n'a pas ete relevee
                    if not result.success:
                        # Exception occured
                        self.waitingThreads[result.parentTid].rWaitingDict[taskKey].result = result.result
                    else:
                        self.waitingThreads[result.parentTid].rWaitingDict[taskKey].result[result.taskIndex] = result.result
                break
            
            assert not foundKey is None        # Debug

            if len(self.waitingThreads[result.parentTid].rWaitingDict[foundKey].tids) == 0:
                # All tasks done
                self.waitingThreads[result.parentTid].rWaitingDict[foundKey].finished = True
                if isinstance(self.waitingThreads[result.parentTid].rWaitingDict[foundKey].result, list):
                    self.waitingThreads[result.parentTid].rWaitingDict[foundKey].success = True
                
                canRestart = False
                if self.waitingThreads[result.parentTid].rWaitingDict[foundKey].waitingOn == True or self.waitingThreads[result.parentTid].waitingMode == DTM_WAIT_ALL:
                    if (self.waitingThreads[result.parentTid].waitingMode == DTM_WAIT_ALL and len(self.waitingThreads[result.parentTid].rWaitingDict) == 1)\
                      or self.waitingThreads[result.parentTid].waitingMode == DTM_WAIT_ANY:
                        canRestart = True
                    elif self.waitingThreads[result.parentTid].waitingMode == DTM_WAIT_SOME:
                        canRestart = True
                        
                        for rKey in self.waitingThreads[result.parentTid].rWaitingDict: 
                            if self.waitingThreads[result.parentTid].rWaitingDict[rKey].waitingOn and rKey != foundKey:
                                canRestart = False
                
                if not self.waitingThreads[result.parentTid].rWaitingDict[taskKey].callbackFunc is None:
                    self.waitingThreads[result.parentTid].rWaitingDict[taskKey].callbackFunc()
                
                if canRestart:
                    wTask = self.waitingThreadsQueue.getSpecificTask(result.parentTid)
                    assert not wTask is None
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
                self.dtmExecLock.acquire(wTask)
                wTask.threadObject.waitingFlag.set()
                taskLauched = True
            except Queue.Empty:
                pass

            if not taskLauched:
                try:
                    newTask = self.execQueue.getTask()
                    newThread = DtmThread(newTask, self)
                    self.dtmExecLock.acquire(newTask)
                    newThread.start()
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
        timeBegin = time.time()
        #print("Control thread on worker " + str(self.workerId) + " :\n PID : " + str(os.getpid()) + "\n PPID : " + str(os.getppid()) + "\n UID : " + str(os.getuid()) + "\n TID? : ")
        #os.system('./getID')
        #print("\n")
        #rem = [time.time()]
        while True:
            
            self.runningFlag.wait()         # ATTENTION, DEADLOCK POSSIBLE
            self.runningFlag.clear()        # Si un thread fait un set() sur le flag entre ces deux lignes!!
            #if self.workerId == 0:
                #rem[-1] = time.time()-rem[-1]
                #rem.append(time.time())
            
            while True:
                try:
                    recvMsg = self.recvQueue.get_nowait()
                    if recvMsg.msgType == DTM_MSG_EXIT:
                        self.exitStatus.set()
                        self.exitState = (recvMsg.msg[1], recvMsg.msg[0])
                        break
                    elif recvMsg.msgType == DTM_MSG_TASK:
                        self.execQueue.putList(recvMsg.msg)
                        self.loadBalancer.updateSelfStatus(self._getLoadTuple())
                        self.sendQueue.put(DtmMessageContainer({'msgType' : DTM_MSG_ACK_RECEIVED_TASK,
                                                        'senderWid' : self.workerId,
                                                        'receiverWid' : recvMsg.senderWid,
                                                        'loadsDict' : self.loadBalancer.getNodesDict(),
                                                        'targetsStats' : self.tasksStats,
                                                        'prepTime' : time.time(),
                                                        'sendTime' : 0,
                                                        'ackNbr' : -1,
                                                        'msg' : recvMsg.ackNbr}))
                        self._updateStats(recvMsg)
                    elif recvMsg.msgType == DTM_MSG_RESULT:
                        self._dispatchResults(recvMsg.msg)
                        self._updateStats(recvMsg)
                    elif recvMsg.msgType == DTM_MSG_REQUEST_TASK:
                        self._updateStats(recvMsg)
                    elif recvMsg.msgType == DTM_MSG_ACK_RECEIVED_TASK:
                        self.loadBalancer.acked(recvMsg.senderWid, recvMsg.msg)
                        self._updateStats(recvMsg)
                    else:
                        _logger.warning("[%s] Unknown message type %s received will be ignored.", str(self.workerId), str(recvMsg.msgType))
                except Queue.Empty:
                    break

	    
            if self.exitStatus.is_set():
                break
            
            #if self.loadmodifiedFlag.is_set():
            # On effectue cette partie seulement si le load a change
            #self.loadmodifiedFlag.clear()       # ATTENTION DEADLOCK
            
            currentNodeStatus = self._getLoadTuple()
            self.loadBalancer.updateSelfStatus(currentNodeStatus)

            sendUpdateList, sendTasksList = self.loadBalancer.takeDecision()
            self.tasksStatsLock.acquire()
            for sendInfo in sendTasksList:
                self.sendQueue.put(DtmMessageContainer({'msgType' : DTM_MSG_TASK,
                                            'senderWid' : self.workerId,
                                            'receiverWid' : sendInfo[0],
                                            'loadsDict' : self.loadBalancer.getNodesDict(),
                                            'targetsStats' : self.tasksStats,
                                            'prepTime' : time.time(),
                                            'sendTime' : 0,
                                            'ackNbr' : sendInfo[2],
                                            'msg' : sendInfo[1]}))

            for updateTo in sendUpdateList:
                self.sendQueue.put(DtmMessageContainer({'msgType' : DTM_MSG_REQUEST_TASK,
                                            'senderWid' : self.workerId,
                                            'receiverWid' : updateTo,
                                            'loadsDict' : self.loadBalancer.getNodesDict(),
                                            'targetsStats' : self.tasksStats,
                                            'prepTime' : time.time(),
                                            'sendTime' : 0,
                                            'ackNbr' : -1,
                                            'msg' : None}))
            self.tasksStatsLock.release()
            self._startNewTask()
            
        #if self.workerId == 0:
            #rem.pop()
            #print rem
            #print(float(sum(rem))/len(rem))
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
        
        try:
            tmpImport = __import__(self.commManagerType, globals(), locals(), ['DtmCommThread'], 0)
            if not hasattr(tmpImport, 'DtmCommThread'):
                raise ImportError
            DtmCommThread = tmpImport.DtmCommThread
        except ImportError:
            _logger.warning("Warning : %s is not a suitable communication manager. Default to commManagerMpi4py.", self.commManagerType)
            tmpImport = __import__('commManagerMpi4py', globals(), locals(), ['DtmCommThread'], 0)
            DtmCommThread = tmpImport.DtmCommThread

        try:
            tmpImport = __import__(self.loadBalancerType, globals(), locals(), ['DtmLoadBalancer'], 0)
            if not hasattr(tmpImport, 'DtmLoadBalancer'):
                raise ImportError
            DtmLoadBalancer = tmpImport.DtmLoadBalancer
        except ImportError:
            _logger.warning("Warning : %s is not a suitable load balancer. Default to loadBalancerPDB.", self.loadBalancerType)
            tmpImport = __import__('loadBalancerPDB', globals(), locals(), ['DtmLoadBalancer'], 0)
            DtmLoadBalancer = tmpImport.DtmLoadBalancer
        
        self.commThread = DtmCommThread(self.recvQueue, self.sendQueue, self.runningFlag, self.commExitNotification, self.commReadyEvent, self.dtmRandom)

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
            
            initTask = DtmTaskContainer({'tid' : self.idGenerator.tid, 
                                    'creatorWid' : self.workerId,
                                    'creatorTid' : None,
                                    'taskIndex' : 0,
                                    'taskRoute' : [self.workerId],
                                    'creationTime' : time.time(),
                                    'target' : initialTarget,
                                    'args' : args,
                                    'kwargs' : kwargs,
                                    'threadObject' : None,
                                    'taskState' : DTM_TASK_STATE_IDLE})
            self.execQueue.put(initTask)

        return self._main()



    # The following methods are NOT called by the control thread, but by the EXECUTION THREADS
    # All the non-local objects used MUST be thread-safe

    def map(self, function, *iterables, **kwargs):
        """
        A parallel equivalent of the `map() <http://docs.python.org/library/functions.html#map>`_ built-in function. It blocks till the result is ready.
        This method chops the iterables into a number of chunks determined by DTM in order to get the most efficient use of the workers.
        It takes any number of iterables (though it will shrink all of them to the len of the smallest one), and any others kwargs that will be
        transmitted as is to the *function* target.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid
        
        zipIterable = list(zip(*iterables))
        
        listResults = [None] * len(zipIterable)
        listTasks = []
        listTids = []
        
        for index,elem in enumerate(zipIterable):
            task = DtmTaskContainer({'tid' : self.idGenerator.tid, 
                                    'creatorWid' : self.workerId,
                                    'creatorTid' : currentId,
                                    'taskIndex' : index,
                                    'taskRoute' : [self.workerId],
                                    'creationTime' : time.time(),
                                    'target' : function,
                                    'args' : elem,
                                    'kwargs' : kwargs,
                                    'threadObject' : None,
                                    'taskState' : DTM_TASK_STATE_IDLE})
            listTasks.append(task)
            listTids.append(task.tid)
        
        self.waitingThreadsLock.acquire()        
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = DtmWaitInfoContainer({'threadObject' : cThread,
                                                    'eventObject' : cThread.waitingFlag,
                                                    'waitBeginningTime' : 0,
                                                    'tasksWaitingCount' : 0,
                                                    'waitingMode' : DTM_WAIT_NONE,
                                                    'rWaitingDict' : {}})
        
        resultKey = listTids[0]
        self.waitingThreads[currentId].rWaitingDict[resultKey] = DtmExceptedResultContainer({'tids' : listTids,
                                'waitingOn' : True,
                                'finished' : False,
                                'success' : False,
                                'callbackFunc' : None,
                                'result' : listResults})
                                
        self.waitingThreads[currentId].tasksWaitingCount += len(listTasks)
        self.waitingThreads[currentId].waitingMode = DTM_WAIT_SOME
        
        
        self.waitingThreadsQueue.put(cThread.taskInfo)
        
        self.waitingThreads[currentId].waitBeginningTime = time.time()
        self.waitingThreadsLock.release()
        
        self.execQueue.putList(listTasks)
        
        
        cThread.waitForResult()

        self.waitingThreadsLock.acquire()
        ret = self.waitingThreads[currentId].rWaitingDict[resultKey].result
        if self.waitingThreads[currentId].rWaitingDict[resultKey].success == False:
            # Exception occured
            del self.waitingThreads[currentId].rWaitingDict[resultKey]
            self.waitingThreadsLock.release()
            raise ret
        else:           
            del self.waitingThreads[currentId].rWaitingDict[resultKey]
            self.waitingThreadsLock.release()
            return ret


    def map_async(self, function, iterable, callback=None):
        """
        A non-blocking variant of the ``DtmControl.map()`` method which returns a result object.
        .. note::
            As on version 0.1, callback is not implemented.
        """
        
        cThread = threading.currentThread()
        currentId = cThread.tid

        listResults = [None] * len(iterable)
        listTasks = []
        listTids = []

        for index,elem in enumerate(iterable):
            task = DtmTaskContainer({'tid' : self.idGenerator.tid, 
                                    'creatorWid' : self.workerId,
                                    'creatorTid' : currentId,
                                    'taskIndex' : index,
                                    'taskRoute' : [self.workerId],
                                    'creationTime' : time.time(),
                                    'target' : function,
                                    'args' : (elem,),
                                    'kwargs' : {},
                                    'threadObject' : None,
                                    'taskState' : DTM_TASK_STATE_IDLE})
            listTasks.append(task)
            listTids.append(task.tid)
        
        resultKey = listTids[0]
               
        self.waitingThreadsLock.acquire()
        
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = DtmWaitInfoContainer({'threadObject' : cThread,
                                                    'eventObject' : cThread.waitingFlag,
                                                    'waitBeginningTime' : 0,
                                                    'tasksWaitingCount' : 0,
                                                    'waitingMode' : DTM_WAIT_NONE,
                                                    'rWaitingDict' : {}})
                                                    
        self.waitingThreads[currentId].rWaitingDict[resultKey] = DtmExceptedResultContainer({'tids' : listTids,
                                'waitingOn' : False,
                                'finished' : False,
                                'success' : False,
                                'callbackFunc' : None,
                                'result' : listResults})

        self.waitingThreads[currentId].waitingMode = DTM_WAIT_NONE
        
        asyncRequest = DtmAsyncResult(self, self.waitingThreads[currentId], resultKey)
        self.waitingThreads[currentId].rWaitingDict[resultKey].callbackFunc = asyncRequest._dtmCallback
        
        self.waitingThreadsLock.release()
        
        self.execQueue.putList(listTasks)
        
        self.runningFlag.set()      # On signale au main thread qu'il s'est passe quelque chose
        
        return asyncRequest


    def apply(self, function, *args, **kwargs):
        """
        Special function that can be used on boot apply() and apply_async()
        Should not be called directly by the user, as apply() do almost the same job.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid
        
        task = DtmTaskContainer({'tid' : self.idGenerator.tid, 
                                    'creatorWid' : self.workerId,
                                    'creatorTid' : currentId,
                                    'taskIndex' : 0,
                                    'taskRoute' : [self.workerId],
                                    'creationTime' : time.time(),
                                    'target' : function,
                                    'args' : args,
                                    'kwargs' : kwargs,
                                    'threadObject' : None,
                                    'taskState' : DTM_TASK_STATE_IDLE})
        self.waitingThreadsLock.acquire()        
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = DtmWaitInfoContainer({'threadObject' : cThread,
                                                    'eventObject' : cThread.waitingFlag,
                                                    'waitBeginningTime' : 0,
                                                    'tasksWaitingCount' : 0,
                                                    'waitingMode' : DTM_WAIT_NONE,
                                                    'rWaitingDict' : {}})
        
        resultKey = task.tid
        
        self.waitingThreads[currentId].rWaitingDict[resultKey] = DtmExceptedResultContainer({'tids' : [task.tid],
                                'waitingOn' : True,
                                'finished' : False,
                                'success' : False,
                                'callbackFunc' : None,
                                'result' : [None]})
        
        self.waitingThreads[currentId].tasksWaitingCount += 1
        self.waitingThreads[currentId].waitingMode = DTM_WAIT_SOME
        
        self.waitingThreadsQueue.put(cThread.taskInfo)
        
        self.waitingThreads[currentId].waitBeginningTime = time.time()
        self.waitingThreadsLock.release()
        
        self.execQueue.put(task)
        

        cThread.waitForResult()

        self.waitingThreadsLock.acquire()
        ret = self.waitingThreads[currentId].rWaitingDict[resultKey].result
        if self.waitingThreads[currentId].rWaitingDict[resultKey].success == False:
            # Exception occured
            del self.waitingThreads[currentId].rWaitingDict[resultKey]
            self.waitingThreadsLock.release()
            raise ret
        else:           
            del self.waitingThreads[currentId].rWaitingDict[resultKey]
            self.waitingThreadsLock.release()
            return ret[0]


    #def apply(self, function, *args, **kwargs):
        #"""
        #Equivalent of the `apply() <http://docs.python.org/library/functions.html#apply>`_ built-in function. It blocks till the result is ready.
        #Given this blocks, `apply_async()` is better suited for performing work in parallel.
        #Additionally, the passed in function is only executed in one of the workers of the pool.
        #"""
        #return self._apply(function, args, kwargs)

    def apply_async(self, function, *args, **kwargs):
        """
        A non-blocking variant of the apply() method which returns a result object.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid
        
        task = DtmTaskContainer({'tid' : self.idGenerator.tid, 
                                    'creatorWid' : self.workerId,
                                    'creatorTid' : currentId,
                                    'taskIndex' : 0,
                                    'taskRoute' : [self.workerId],
                                    'creationTime' : time.time(),
                                    'target' : function,
                                    'args' : args,
                                    'kwargs' : kwargs,
                                    'threadObject' : None,
                                    'taskState' : DTM_TASK_STATE_IDLE})
        self.waitingThreadsLock.acquire()        
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = DtmWaitInfoContainer({'threadObject' : cThread,
                                                    'eventObject' : cThread.waitingFlag,
                                                    'waitBeginningTime' : 0,
                                                    'tasksWaitingCount' : 0,
                                                    'waitingMode' : DTM_WAIT_NONE,
                                                    'rWaitingDict' : {}})
        
        resultKey = task.tid
        
        self.waitingThreads[currentId].rWaitingDict[resultKey] = DtmExceptedResultContainer({'tids' : [task.tid],
                                'waitingOn' : False,
                                'finished' : False,
                                'success' : False,
                                'callbackFunc' : None,
                                'result' : [None]})
        
        self.waitingThreads[currentId].waitingMode = DTM_WAIT_NONE
        
        asyncRequest = DtmAsyncResult(self, self.waitingThreads[currentId], resultKey)
        self.waitingThreads[currentId].rWaitingDict[resultKey].callbackFunc = asyncRequest._dtmCallback
        
        self.waitingThreadsLock.release()
        
        self.execQueue.put(task)
        
        self.runningFlag.set()
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
            for i in range(currentIndex, maxIndex):
                asyncResults[i%chunksize] = self.apply_async(function, iterable[i])

            for result in asyncResults:
                ret = result.get()
                yield ret

            currentIndex = maxIndex


    def imap_unordered(self, function, iterable, chunksize=1):
        # Cette implementation a un probleme : contrairement a imap(),
        # on n'attend pas un resultat specifique, mais n'importe lequel
        # Idealement, il faudrait implementer un dtm.waitAny()
        #TODO
        raise NotImplementedError


    def filter(self, function, iterable):
        # Le filtrage s'effectue dans ce thread, mais le calcul est distribue
        results = self.map(function, iterable)
        return [item for result, item in zip(results, iterable) if result]

    def repeat(self, function, howManyTimes, *args, **kwargs):
        # Repete une fonction avec les memes arguments et renvoie une liste contenant les resultats
        
        cThread = threading.currentThread()
        currentId = cThread.tid

        listResults = [None] * howManyTimes
        listTasks = []
        listTids = []
        
        for index in range(howManyTimes):
            task = DtmTaskContainer({'tid' : self.idGenerator.tid, 
                                    'creatorWid' : self.workerId,
                                    'creatorTid' : currentId,
                                    'taskIndex' : index,
                                    'taskRoute' : [self.workerId],
                                    'creationTime' : time.time(),
                                    'target' : function,
                                    'args' : args,
                                    'kwargs' : kwargs,
                                    'threadObject' : None,
                                    'taskState' : DTM_TASK_STATE_IDLE})
            listTasks.append(task)
            listTids.append(task.tid)
        
        self.waitingThreadsLock.acquire()        
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = DtmWaitInfoContainer({'threadObject' : cThread,
                                                    'eventObject' : cThread.waitingFlag,
                                                    'waitBeginningTime' : 0,
                                                    'tasksWaitingCount' : 0,
                                                    'waitingMode' : DTM_WAIT_NONE,
                                                    'rWaitingDict' : {}})
        
        resultKey = listTids[0]
        self.waitingThreads[currentId].rWaitingDict[resultKey] = DtmExceptedResultContainer({'tids' : listTids,
                                'waitingOn' : True,
                                'finished' : False,
                                'success' : False,
                                'callbackFunc' : None,
                                'result' : listResults})
                                
        self.waitingThreads[currentId].tasksWaitingCount += len(listTasks)
        self.waitingThreads[currentId].waitingMode = DTM_WAIT_SOME
        
        
        self.waitingThreadsQueue.put(cThread.taskInfo)
        
        self.waitingThreads[currentId].waitBeginningTime = time.time()
        self.waitingThreadsLock.release()
        
        self.execQueue.putList(listTasks)
        
        
        cThread.waitForResult()

        self.waitingThreadsLock.acquire()
        ret = self.waitingThreads[currentId].rWaitingDict[resultKey].result
        if self.waitingThreads[currentId].rWaitingDict[resultKey].success == False:
            # Exception occured
            del self.waitingThreads[currentId].rWaitingDict[resultKey]
            self.waitingThreadsLock.release()
            raise ret
        else:           
            del self.waitingThreads[currentId].rWaitingDict[resultKey]
            self.waitingThreadsLock.release()
            return ret

    def waitForAll(self):
        # Met le thread en pause et attend TOUS les resultats asynchrones
        threadId = threading.currentThread().tid
        
        self.waitingThreadsLock.acquire()
        if threadId in self.waitingThreads and len(self.waitingThreads[threadId].rWaitingDict) > 0:
            self.waitingThreads[threadId].waitingMode = DTM_WAIT_ALL
            self.waitingThreadsQueue.put(threading.currentThread().taskInfo)
            self.waitingThreadsLock.release()
            threading.currentThread().waitForResult()
            
            self.waitingThreadsLock.acquire()
            self.waitingThreads[threadId].waitingMode = DTM_WAIT_NONE           
            self.waitingThreadsLock.release()
        else:            
            self.waitingThreadsLock.release()
            return        
        return None

    def testAllAsync(self):
        # Teste si tous les taches asynchrones sont terminees
        threadId = threading.currentThread().tid
        self.waitingThreadsLock.acquire()
        if threadId in self.waitingThreads:
            ret = len(self.waitingThreads[threadId].rWaitingDict)
            self.waitingThreadsLock.release()
            return False
        else:
            self.waitingThreadsLock.release()
            return True


    def getWorkerId(self):
        # With MPI, return the slot number
        return self.workerId




class DtmThread(threading.Thread):
    """
    Les threads d'execution sont la base de DTM
    Leur particularite principale est de posseder un lock conditionnel unique
    qui permet d'arreter/repartir le thread lors des appels a DTM
    """
    def __init__(self, structInfo, controlThread):
        threading.Thread.__init__(self)
        
        self.taskInfo = structInfo      # DtmTaskContainer
        
        self.taskInfo.threadObject = self   # Remind that we are the exec thread
        
        self.tid = structInfo.tid
        self.t = structInfo.target
        self.control = controlThread

        self.waitingFlag = threading.Event()        
        self.waitingFlag.clear()
        
        self.timeExec = 0
        self.timeBegin = 0
        if structInfo.creatorTid is None:
            self.isRootTask = True
        else:
            self.isRootTask = False

    def run(self):
        # On s'assure qu'aucun autre thread ne s'execute
        #self.control.dtmExecLock.acquire()     # Le lock est deja acquis pour nous
        self.taskInfo.taskState = DTM_TASK_STATE_RUNNING
        success = True
        self.timeBegin = time.time()
        try:
            returnedR = self.t(*self.taskInfo.args, **self.taskInfo.kwargs)
        except Exception as expc:
            returnedR = expc
            success = False
            
        # Pour le debug, on VEUT voir les exceptions
        #returnedR = self.t(*self.taskInfo.args, **self.taskInfo.kwargs)
        
        self.timeExec += time.time() - self.timeBegin
        
        self.control.dtmExecLock.release()
        if success:
            try:
                self.control._addTaskStat(self.t.__name__, self.timeExec)
            except AttributeError:
                self.control._addTaskStat(str(self.t), self.timeExec)

        
        if self.isRootTask:
            # Si la tache racine est terminee alors on quitte
            self.control.lastRetValue = (success, returnedR)
            self.control.exitSetHere = True
            self.control.exitStatus.set()
        else:
            # Sinon on retourne le resultat
            resultStruct = DtmResultContainer({'tid' : self.tid,
                                            'parentTid' : self.taskInfo.creatorTid,
                                            'taskIndex' : self.taskInfo.taskIndex,
                                            'execTime' : self.timeExec,
                                            'success' : success,
                                            'result' : returnedR})
                                            
            self.control._returnResult(self.taskInfo.creatorWid, resultStruct)

        # On informe le main thread qu'on a du nouveau
        self.control._startNewTask()
        
        if self.isRootTask:
            self.control.runningFlag.set()
        
        self.control.waitingThreadsLock.acquire()
        if self.tid in self.control.waitingThreads.keys():
            del self.control.waitingThreads[self.tid]
        self.control.waitingThreadsLock.release()
        self.taskInfo.taskState = DTM_TASK_STATE_FINISH
    

    def waitForResult(self):
        # Libere le lock d'execution et attend que la condition soit remplie pour continuer
        beginTimeWait = time.time()
        self.timeExec += beginTimeWait - self.timeBegin
        self.control.dtmExecLock.release()
        
        self.taskInfo.taskState = DTM_TASK_STATE_WAITING
        
        # On tente de lancer tout de suite une nouvelle tache
        self.control._startNewTask()
        self.control.runningFlag.set()
        
        self.waitingFlag.wait()        
        self.waitingFlag.clear()

        #self.control.dtmExecLock.acquire()     # Le lock est deja acquis pour nous
        self.taskInfo.taskState = DTM_TASK_STATE_RUNNING
        self.timeBegin = time.time()




class DtmAsyncResult(object):
    """
    The class of the result returned by **DtmControl.map_async()** and **DtmControl.apply_async()**.
    """
    def __init__(self, control, waitingInfo, taskKey):
        self.control = control
        self.resultReturned = False
        self.resultSuccess = False
        self.resultVal = None
        self.taskKey = taskKey
        self.dictWaitingInfo = waitingInfo
        
    
    def _dtmCallback(self):
        # Used by DTM to inform the object that the job is done
        self.resultSuccess = self.dictWaitingInfo.rWaitingDict[self.taskKey].success
        self.resultVal = self.dictWaitingInfo.rWaitingDict[self.taskKey].result
        self.resultReturned = True
        
        del self.dictWaitingInfo.rWaitingDict[self.taskKey]


    def get(self):
        """
        Return the result when it arrives.
        .. note::
            This is a blocking call : caller will wait in this function until the result is ready.
            To check for the avaibility of the result, use ready()
        """
        if not self.resultReturned:
            self.wait()
        
        if self.resultSuccess:
            return self.resultVal
        else:
            raise self.resultVal

    def wait(self):
        """
        Wait until the result is available
        """
        
        self.control.waitingThreadsLock.acquire()
        
        if self.ready():
            # Il est IMPORTANT que ce bloc soit protege par le mutex
            # On ne veut pas que le mainthread ecrive le resultat
            # Tant qu'on a pas signifie qu'on est en wait
            self.control.waitingThreadsLock.release()
            return
        
        self.control.waitingThreads[threading.currentThread().tid].waitingMode = DTM_WAIT_SOME
        self.control.waitingThreads[threading.currentThread().tid].rWaitingDict[self.taskKey].waitingOn = True
        #self.dictWaitingInfo.waitingMode = DTM_WAIT_SOME
        #self.dictWaitingInfo.rWaitingDict[self.taskKey].waitingOn = True
        self.control.waitingThreadsQueue.put(threading.currentThread().taskInfo)
        self.control.waitingThreadsLock.release()

        threading.currentThread().waitForResult()


    def ready(self):
        """
        Return whether the asynchronous task has completed.
        """
        return self.resultReturned

    def successful(self):
        """
        Return whether the task completed without error. Will raise AssertionError if the result is not ready.
        """
        if not self.resultReturned:
            raise AssertionError("Call DtmAsyncResult.successful() before the results were ready!")
        return self.resultSuccess


dtm = DtmControl()
