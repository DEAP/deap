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
import os
import traceback

PRETTY_PRINT_SUPPORT = False
try:
    from lxml import etree
    PRETTY_PRINT_SUPPORT = True
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        # Python 2.5
        import xml.etree.ElementTree as etree

from deap.dtm.dtmTypes import *

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
_logger = logging.getLogger("dtm.control")

# Constantes
DTM_CONTROL_THREAD_LATENCY = 0.05

MSG_COMM_TYPE = 0
MSG_SENDER_INFO = 1
MSG_NODES_INFOS = 2

DTM_LOGDIR_DEFAULT_NAME = "DtmLog"

try:
    from math import erf
except ImportError:
    def erf(x):
        # See http://stackoverflow.com/questions/457408/is-there-an-easily-available-implementation-of-erf-for-python
        # save the sign of x
        sign = 1
        if x < 0:
            sign = -1
        x = abs(x)

        # constants
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        # A&S formula 7.1.26
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
        return sign * y # erf(-x) = -erf(x)


class TaskIdGenerator(object):
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


class ExecInfo(object):
    """
    Contains the information about the current task
    """
    def __init__(self, tStats, tStatsLock):
        self.eLock = threading.Lock()
        self.tStats = tStats
        self.tStatsLock = tStatsLock
        self.eCurrent = None
        self.mainThread = threading.currentThread()
        self.piSqrt = math.sqrt(math.pi)
        self.sqrt2 = 2 ** 0.5

    def _execTimeRemaining(self, mean, stdDev, alreadyDone):
        if alreadyDone == 0.:
            # If not started yet, return mean
            return mean
        if stdDev == 0.:
            # Only one result (or a very very very little variation...)
            return mean-alreadyDone if mean-alreadyDone > 0 else 1.
        #
        # Else compute the mass center of the remaining part of the gaussian
        # For instance, if we have a gaussian (mu, sigma) = (3, 4)
        # and that the task is executing for 3 seconds, then we may estimate
        # that it will probably finished at :
        # int(x*gaussian) / int(gaussian) over [3, +inf[
        # (where int is integral)
        #
        # We get 6.192 seconds, that is an expected remaining time of
        # 6.192 - 3 = 3.192 seconds

        # Evaluate primitive at point 'alreadyDone'
        commonPart = erf(self.sqrt2 * (alreadyDone - mean) / (stdDev * 2))
        areaPart1 = 0.5 * commonPart
        massCenterPart1 = (self.sqrt2 / (4 * self.piSqrt)) * (-2 * stdDev * math.exp(-0.5 * ((alreadyDone - mean) ** 2) / (stdDev ** 2)) + mean * (self.piSqrt) * (self.sqrt2) * commonPart)

        # Evaluate primitive at the infinite
        # erf(+inf) = 1, so
        areaPart2 = 0.5
        # exp(-inf) = 0, and erf(+inf) = 1, so
        massCenterPart2 = mean / 2.

        if areaPart1 == areaPart2:
            # So far from the mean that erf(alreadyDone - moyenne) = 1
            previsionPoint = alreadyDone + 0.5      # Hack : lets assume that there's 0.5 sec left...
        else:
            previsionPoint = (massCenterPart2 - massCenterPart1) / (areaPart2 - areaPart1)

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
        cumulativeLoad = 0.
        try:
            self.tStatsLock.acquire()
            # Assuming that every subtasks are the same
            try:
                tInfo = self.tStats.get(str(self.eCurrent.target[0].__name__), StatsContainer(rAvg=1., rStdDev=1., rSquareSum=0., spawnSubtasks=False, execCount=0))
            except AttributeError:
                tInfo = self.tStats.get(self.eCurrent.target[0], StatsContainer(rAvg=1., rStdDev=1., rSquareSum=0., spawnSubtasks=False, execCount=0))

            val = self._execTimeRemaining(tInfo.rAvg, tInfo.rStdDev, self.eCurrent.threadObject.timeExec) * len(self.eCurrent.target)
            self.tStatsLock.release()
            return val
        except AttributeError:
            self.tStatsLock.release()
            return 0.


class TaskQueue(object):
    """
    """
    def __init__(self, tasksStatsStruct, tasksStatsLock, controlObject):
        self.tStats = tasksStatsStruct
        self.tStatsLock = tasksStatsLock
        self.previousLoad = 0.
        self.piSqrt = math.sqrt(math.pi)
        self.sqrt2 = 2 ** 0.5
        self._tQueue = Queue.PriorityQueue()
        self._tDict = {}
        self._actionLock = threading.Lock()
        self.changed = True
        self.control = controlObject

    def _getTimeInfoAbout(self, task):
        if task.threadObject is None:
            timeDone = 0.
        else:
            timeDone = task.threadObject.timeExec

        self.tStatsLock.acquire()
        # Assuming that every subtasks are the same
        try:
            tInfo = self.tStats.get(str(task.target[0].__name__), StatsContainer(rAvg=1., rStdDev=1., rSquareSum=0., spawnSubtasks=False, execCount=0))
        except AttributeError:
            tInfo = self.tStats.get(task.target[0], StatsContainer(rAvg=1., rStdDev=1., rSquareSum=0., spawnSubtasks=False, execCount=0))

        self.tStatsLock.release()

        return self._execTimeRemaining(tInfo.rAvg, tInfo.rStdDev, timeDone) * len(task.target)

    def _execTimeRemaining(self, mean, stdDev, alreadyDone):
        if alreadyDone == 0. or stdDev == 0:
            return mean

        #
        # Else compute the mass center of the remaining part of the gaussian
        # For instance, if we have a gaussian (mu, sigma) = (3, 4)
        # and that the task is executing for 3 seconds, then we may estimate
        # that it will probably finished at :
        # int(x*gaussian) / int(gaussian) over [3, +inf[
        # (where int is integral)
        #
        # We get 6.192 seconds, that is an expected remaining time of
        # 6.192 - 3 = 3.192 seconds

        # Evaluate primitive at point 'alreadyDone'
        commonPart = erf(self.sqrt2 * (alreadyDone - mean) / (stdDev * 2))
        areaPart1 = 0.5 * commonPart
        massCenterPart1 = (self.sqrt2 / (4 * self.piSqrt)) * (-2 * stdDev * math.exp(-0.5 * ((alreadyDone - mean) ** 2) / (stdDev ** 2)) + mean * (self.piSqrt) * (self.sqrt2) * commonPart)

        # Evaluate primitive at the infinite
        # erf(+inf) = 1, so
        areaPart2 = 0.5
        # exp(-inf) = 0, and erf(+inf) = 1, so
        massCenterPart2 = mean / 2.

        if areaPart1 == areaPart2:
            # So far from the mean that erf(alreadyDone - moyenne) = 1
            previsionPoint = alreadyDone + 0.5      # Hack : lets assume that there's 0.5 sec left...
        else:
            previsionPoint = (massCenterPart2 - massCenterPart1) / (areaPart2 - areaPart1)

        return previsionPoint - alreadyDone

    def put(self, taskObject):
        self.putList((taskObject,))

    def putList(self, tasksList):
        self._actionLock.acquire()

        logRoute = True if hasattr(tasksList[0],'taskRoute') else False

        for taskObject in tasksList:
            if logRoute:
                taskObject.taskRoute.append(self.control.workerId)
            self._tDict[taskObject.tid] = taskObject
            self._tQueue.put(taskObject)

        self.changed = True
        self._actionLock.release()

    def getTask(self):
        self._actionLock.acquire()
        while True:
            try:
                taskObject = self._tQueue.get_nowait()
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

        for tid, tObj in self._tDict.items():
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

    def getTaskByExecTime(self, execTimeWanted, maxDiff= -1.):
        # maxDiff is the max difference wanted
        # If there is no task with the execTimeWanted +- maxDiff,
        # return None
        # maxDiff = -1 means that there is no max difference
        mostClose = None
        self._actionLock.acquire()

        for tid, tObj in self._tDict.items():
            timeDiff = math.abs(execTimeWanted - self._getTimeInfoAbout(tObj))
            if mostClose is None or mostClose[1] > timeDiff:
                mostClose = (tid, timeDiff)

        self._actionLock.release()

        if mostClose is None or (maxDiff >= 0 and mostClose[1] > maxDiff):
            return None
        else:
            return self.getSpecificTask(mostClose[0])

    def getTasksIDsWithExecTime(self, execTimeWanted, maxDiff= -1.):
        # Return task list containing tasks which the durations approximately
        # sum to execTimeWanted
        returnList = []
        totalTime = 0.
        self._actionLock.acquire()

        for tid, tObj in self._tDict.items():
            timeInfo = self._getTimeInfoAbout(tObj)
            if totalTime + timeInfo <= execTimeWanted:
                returnList.append(tid)
                totalTime += timeInfo
        #
        # Hack to avoid the starting bug (few jobs but very long)
        #
        if len(returnList) == 0 and maxDiff == -1 and len(self._tDict) > 1:
            it = filter(lambda x: self._getTimeInfoAbout(x[1]) != 0, self._tDict.items())
            if len(it) != 0:
                returnList.append(it[0][0])
                totalTime += self._getTimeInfoAbout(it[0][1])
        self._actionLock.release()
        return returnList, totalTime



class Control(object):
    """
    Control is the main DTM class. The dtm object you receive when you use ``from deap import dtm``
    is a proxy over an instance of this class.

    Most of its methods are used by your program, in the execution tasks; however, two of thems (start() and setOptions()) MUST be called
    in the MainThread (i.e. the thread started by the Python interpreter).

    As this class is instancied directly in the module, initializer takes no arguments.
    """
    def __init__(self):
        self.sTime = time.time()

        # Key : Target, Value : StatsContainer
        self.tasksStats = {}
        self.tasksStatsLock = threading.Lock()

        # Global execution lock
        self.dtmExecLock = ExecInfo(self.tasksStats, self.tasksStatsLock)

        self.waitingThreadsQueue = TaskQueue(self.tasksStats, self.tasksStatsLock, self)

        # Key : task ID, Value : WaitInfoContainer
        self.waitingThreads = {}
        self.waitingThreadsLock = threading.Lock()


        self.launchTaskLock = threading.Lock()

        self.waitingForRestartQueue = TaskQueue(self.tasksStats, self.tasksStatsLock, self)
        self.execQueue = TaskQueue(self.tasksStats, self.tasksStatsLock, self)

        self.recvQueue = Queue.Queue()      # Contains MessageContainer
        self.sendQueue = Queue.Queue()      # Contains MessageContainer

        self.exitStatus = threading.Event()
        self.commExitNotification = threading.Event()
        self.commReadyEvent = threading.Event()

        self.exitState = (None, None)
        self.exitSetHere = False

        # Will stop the main thread until an event occurs
        self.runningFlag = threading.Event()
        self.runningFlag.set()

        self.commManagerType = "deap.dtm.commManagerMpi4py"
        self.loadBalancerType = "deap.dtm.loadBalancerPDB"
        self.printExecSummary = True

        self.isStarted = False

        self.traceMode = False
        self.traceDir = DTM_LOGDIR_DEFAULT_NAME
        self.traceRoot = None   # Root element of the XML log
        self.traceTasks = None  # XML elements
        self.traceComm = None   # defined if traceMode == True
        self.traceLoadB = None
        self.traceStats = None
        self.traceLock = threading.Lock()

        self.refTime = 1.

        self.loadBalancer = None

        self.mapChunkSize = 1

        self.serializeSmallTasks = False
        self.minGranularity = 0.

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
                self.sendQueue.put(MessageContainer(msgType = DTM_MSG_EXIT,
                                    senderWid = self.workerId,
                                    receiverWid = n,
                                    loadsDict = None,
                                    targetsStats = None,
                                    prepTime = time.time(),
                                    sendTime = 0,
                                    ackNbr = -1,
                                    msg = (0, "Exit with success")))

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
                for target, times in self.tasksStats.items():
                    msgT += "\t" + str(target) + " : Avg=" + str(times.rAvg * self.refTime) + ", StdDev=" + str(times.rStdDev * self.refTime) + "\n\n"
                _logger.info(msgT)

            _logger.info("DTM execution ended (no more tasks)")
            _logger.info("Total execution time : %s", str(time.time() - self.sTime))

        if self.traceMode:
            _logger.info("Writing log to the log files...")
            self.traceLock.acquire()
            fstat = etree.SubElement(self.traceRoot, "finalStats")
            for target, times in self.tasksStats.items():
                etree.SubElement(fstat, "taskinfo", {"target" : str(target), "avg" : repr(times.rAvg * self.refTime), "stddev" : repr(times.rStdDev * self.refTime), "execcount" : str(times.execCount)})

            flog = open(self.traceDir + "/log" + str(self.workerId) + ".xml", 'w')
            if PRETTY_PRINT_SUPPORT:
                flog.write(etree.tostring(self.traceRoot, pretty_print=True))
            else:
                flog.write(etree.tostring(self.traceRoot))
            flog.close()
            self.traceLock.release()

        if self.exitSetHere:
            if self.lastRetValue[0]:
                return self.lastRetValue[1][0]
            else:
                raise self.lastRetValue[1]


    def _logTaskStatChange(self):
        # Assume that we own the tasksStatsLock before calling

        self.traceLock.acquire()
        statsLog = etree.SubElement(self.traceStats, "timeInfo", {"time" : repr(time.time())})
        for taskTarget, taskInfo in self.tasksStats.items():
            try:
                etree.SubElement(statsLog, "target", {"name" : str(taskTarget.__name__), "execCount" : repr(taskInfo.execCount),
                                                    "avgExecTime" : repr(taskInfo.rAvg), "stdDevExecTime" : repr(taskInfo.rStdDev)})
            except AttributeError:
                etree.SubElement(statsLog, "target", {"name" : taskTarget, "execCount" : repr(taskInfo.execCount),
                                            "avgExecTime" : repr(taskInfo.rAvg), "stdDevExecTime" : repr(taskInfo.rStdDev)})

        self.traceLock.release()

    def _addTaskStat(self, taskKey, timeExec, spawnedTasks):
        # The execution time is based on the calibration ref time
        comparableLoad = timeExec / self.refTime
        # We do not keep up all the execution times, but
        # update the mean and stddev realtime

        self.tasksStatsLock.acquire()
        if not taskKey in self.tasksStats:
            self.tasksStats[taskKey] = StatsContainer(rAvg = timeExec,
                                                rStdDev = 0.,
                                                rSquareSum = timeExec * timeExec,
                                                spawnSubtasks=spawnedTasks,
                                                execCount = 1)
        else:
            oldAvg = self.tasksStats[taskKey].rAvg
            oldStdDev = self.tasksStats[taskKey].rStdDev
            oldSum2 = self.tasksStats[taskKey].rSquareSum
            oldExecCount = self.tasksStats[taskKey].execCount
            oldSpawSubtasks = self.tasksStats[taskKey].spawnSubtasks

            self.tasksStats[taskKey].rAvg = (timeExec + oldAvg * oldExecCount) / (oldExecCount + 1)
            self.tasksStats[taskKey].rSquareSum = oldSum2 + timeExec * timeExec
            self.tasksStats[taskKey].rStdDev = abs(self.tasksStats[taskKey].rSquareSum / (oldExecCount + 1) - self.tasksStats[taskKey].rAvg ** 2) ** 0.5
            self.tasksStats[taskKey].execCount = oldExecCount + 1
            self.tasksStats[taskKey].spawnSubtasks = True if oldSpawSubtasks or spawnedTasks else False

        if self.traceMode:
            self._logTaskStatChange()

        self.tasksStatsLock.release()

    def _getChunkSize(self, taskTarget):
        """
        Get the optimal chunk size for a parallel map/repeat
        It may have been set by the user with the option mapChunkSize
        or it may be dynamic (with the option serializeSmallTasks).
        In any other case, this function returns 1 (1 task by object).
        Should not be called by user
        """
        if self.serializeSmallTasks:
            try:
                taskKey = taskTarget.__name__
            except AttributeError:
                taskKey = str(taskTarget)

            self.tasksStatsLock.acquire()

            if not taskKey in self.tasksStats:
                # If we don't know anything about the task, we assume that
                # we can't make bigger chunks
                self.tasksStatsLock.release()
                return self.mapChunkSize

            taskStats = self.tasksStats[taskKey]
            self.tasksStatsLock.release()

            # Criteria to chunk : avg exec time < 2 * minGranularity
            # Another important criteria is to check if the task
            # spawn other sub tasks
            if not taskStats.spawnSubtasks and taskStats.rAvg*2 <= self.minGranularity:
                # if taskStats.rStdDev < taskStats.rAvg ...
                return int(self.minGranularity/taskStats.rAvg)

        return self.mapChunkSize


    def _calibrateExecTime(self, runsN=3):
        """
        Small calibration test, run at startup
        Should not be called by user
        """
        timesList = []
        for r in range(runsN):
            timeS = time.clock()

            a = 0.
            for i in range(10000):
                a = math.sqrt(self.dtmRandom.random() / (self.dtmRandom.uniform(0, i) + 1))

            strT = ""
            for i in range(5000):
                strT += str(self.dtmRandom.randint(0, 9999))

            for i in range(500):
                pickStr = pickle.dumps(strT)
                strT = pickle.loads(pickStr)

            timesList.append(time.clock() - timeS)

        return sorted(timesList)[int(runsN / 2)]


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
            self.sendQueue.put(MessageContainer(msgType = DTM_MSG_RESULT,
                                            senderWid = self.workerId,
                                            receiverWid = idToReturn,
                                            loadsDict = self.loadBalancer.getNodesDict(),
                                            targetsStats = self.tasksStats,
                                            prepTime = time.time(),
                                            sendTime = 0,
                                            ackNbr = -1,
                                            msg = (resultInfo,)))

    def _updateStats(self, msg):
        """
        Called by the control thread to update its dictionnary
        Should NOT be called explicitly by the user
        """
        self.loadBalancer.mergeNodeStatus(msg.loadsDict)

        self.tasksStatsLock.acquire()

        for key, val in msg.targetsStats.items():
            if key == "spawnSubtasks" and (self.tasksStats[key] or val.spawnSubtasks):
                self.tasksStats[key] = True
                continue    # We do not want to change the confirmation that the task spawns others

            if not key in self.tasksStats or val.execCount > self.tasksStats[key].execCount:
                self.tasksStats[key] = val

        if self.traceMode:
            self._logTaskStatChange()

        self.tasksStatsLock.release()


    def _dispatchResults(self, resultsList):
        """
        Called by the control thread when a message is received;
        Dispatch it to the task waiting for it.
        Should NOT be called explicitly by the user
        """
        for result in resultsList:
            self.waitingThreadsLock.acquire()

            # We look for the task waiting for each result
            foundKey = None
            for taskKey in self.waitingThreads[result.parentTid].rWaitingDict:
                try:
                    self.waitingThreads[result.parentTid].rWaitingDict[taskKey].tids.remove(result.tid)
                except ValueError:
                    # The ID is not in this waiting list, continue with other worker
                    continue

                foundKey = taskKey
                # Check if an exception as previously occurs on the same task (we do not want to erase it)
                if isinstance(self.waitingThreads[result.parentTid].rWaitingDict[taskKey].result, list):
                    for taskIndex,success,resultValue in zip(result.taskIndex,result.success,result.result):
                        if not success:
                            # Exception occured
                            self.waitingThreads[result.parentTid].rWaitingDict[taskKey].result = result.result
                            break
                        else:
                            self.waitingThreads[result.parentTid].rWaitingDict[taskKey].result[taskIndex] = resultValue
                break

            assert not foundKey is None, "Parent task not found for result dispatch!"        # Debug

            if len(self.waitingThreads[result.parentTid].rWaitingDict[foundKey].tids) == 0:
                # All sub-tasks done

                self.waitingThreads[result.parentTid].rWaitingDict[foundKey].finished = True
                # To be replaced by a better check : here, we actually check if an exception as occurred,
                # because if not, the result will always be a list... but this is absolutely not clear...
                # We cannot use 'if not issubclass(..., Exception)' because issubclass can not work with
                # other objects than classes...
                if isinstance(self.waitingThreads[result.parentTid].rWaitingDict[foundKey].result, list):
                    self.waitingThreads[result.parentTid].rWaitingDict[foundKey].success = True

                canRestart = True

                if self.waitingThreads[result.parentTid].waitingMode == DTM_WAIT_ALL:
                    self.waitingThreads[result.parentTid].rWaitingDict[foundKey].waitingOn = False
                    for waitingTaskId in self.waitingThreads[result.parentTid].rWaitingDict:
                        if self.waitingThreads[result.parentTid].rWaitingDict[waitingTaskId].waitingOn:
                            canRestart = False
                            break
                elif self.waitingThreads[result.parentTid].waitingMode == DTM_WAIT_ANY:
                    if self.waitingThreads[result.parentTid].rWaitingDict[foundKey].waitingOn:
                        for waitingTaskId in self.waitingThreads[result.parentTid].rWaitingDict:
                            self.waitingThreads[result.parentTid].rWaitingDict[waitingTaskId].waitingOn = False
                    else:
                        canRestart = False
                else:
                    # No waiting (asynchronous)
                    canRestart = False

                taskAsyncObj = self.waitingThreads[result.parentTid].rWaitingDict[foundKey].callbackClass
                if not taskAsyncObj is None:
                    taskAsyncObj._dtmCallback()

                if canRestart:
                    self.waitingThreads[result.parentTid].waitingMode = DTM_WAIT_NONE
                    wTask = self.waitingThreadsQueue.getSpecificTask(result.parentTid)
                    assert not wTask is None, "Parent task not present in waitingThreadsQueue!"

                    if not taskAsyncObj is None:
                        wTask.lastSubTaskDone = taskAsyncObj
                        wTask.threadObject.asyncTasksDoneList.append(foundKey)
                    self.waitingForRestartQueue.put(wTask)
                else:
                    self.waitingThreads[result.parentTid].threadObject.taskInfo.lastSubTaskDone = taskAsyncObj
                    self.waitingThreads[result.parentTid].threadObject.asyncTasksDoneList.append(foundKey)

            self.waitingThreadsLock.release()



    def _startNewTask(self):
        """
        Start a new task (if there's one available)
        Return True if so
        Should NOT be called explicitly by the user
        """
        taskLaunched = False
        self.launchTaskLock.acquire()
        if not self.dtmExecLock.isLocked():
            try:
                wTask = self.waitingForRestartQueue.getTask()
                self.dtmExecLock.acquire(wTask)
                wTask.threadObject.waitingFlag.set()
                taskLaunched = True
            except Queue.Empty:
                pass

            if not taskLaunched:
                try:
                    newTask = self.execQueue.getTask()
                    if self.traceMode:
                        self.traceLock.acquire()
                        newTaskElem = etree.SubElement(self.traceTasks, "task",
                                                       {"id" : str(newTask.tid),
                                                        "creatorTid" : str(newTask.creatorTid),
                                                        "creatorWid" : str(newTask.creatorWid),
                                                        "taskIndex" : str(newTask.taskIndex)[1:-1],
                                                        "creationTime" : repr(newTask.creationTime)})
                        try:
                            newTaskTarget = etree.SubElement(newTaskElem, "target",
                                                         {"name" : str(newTask.target[0].__name__)})
                        except AttributeError:
                            newTaskTarget = etree.SubElement(newTaskElem, "target",
                                                         {"name" : str(newTask.target[0])})

                        # TODO TO BE UPDATED (args and kwargs are list of args...)
                        for i, a in enumerate(zip(*newTask.args)):
                            newTaskTarget.set("arg" + str(i), str(a)[1:-1])
                        for k in newTask.kwargs[0]:
                            newTaskTarget.set("kwarg_" + str(k), str([newTask.kwargs[i][k] for i in xrange(len(newTask.kwargs))]))

                        newTaskPath = etree.SubElement(newTaskElem, "path", {"data" : str(newTask.taskRoute)[1:-1]})
                        self.traceLock.release()

                        newThread = DtmThread(newTask, self, newTaskElem)
                    else:
                        newThread = DtmThread(newTask, self)
                    self.dtmExecLock.acquire(newTask)
                    newThread.start()
                    taskLaunched = True
                except Queue.Empty:
                    pass

        self.launchTaskLock.release()
        if taskLaunched:
            self.loadBalancer.updateSelfStatus(self._getLoadTuple())

        return taskLaunched

    def _main(self):
        """
        Main loop of the control thread
        Should NOT be called explicitly by the user
        """

        timeBegin = time.time()
        while True:

            self.runningFlag.wait()         # WARNING, may deadlock on very specific conditions
            self.runningFlag.clear()        # (if the _last_ task do a set() between those 2 lines, nothing will wake up the main thread)

            while True:
                try:
                    recvMsg = self.recvQueue.get_nowait()
                    if recvMsg.msgType == DTM_MSG_EXIT:
                        self.exitStatus.set()
                        self.exitState = (recvMsg.msg[1], recvMsg.msg[0])
                        break
                    elif recvMsg.msgType == DTM_MSG_TASK:
                        self.execQueue.putList(recvMsg.msg)
                        self.sendQueue.put(MessageContainer(msgType = DTM_MSG_ACK_RECEIVED_TASK,
                                                        senderWid = self.workerId,
                                                        receiverWid = recvMsg.senderWid,
                                                        loadsDict = self.loadBalancer.getNodesDict(),
                                                        targetsStats = self.tasksStats,
                                                        prepTime = time.time(),
                                                        sendTime = 0,
                                                        ackNbr = -1,
                                                        msg = recvMsg.ackNbr))
                        self._updateStats(recvMsg)
                        self.loadBalancer.updateSelfStatus(self._getLoadTuple())
                    elif recvMsg.msgType == DTM_MSG_RESULT:
                        self._updateStats(recvMsg)
                        self._dispatchResults(recvMsg.msg)
                    elif recvMsg.msgType == DTM_MSG_REQUEST_TASK:
                        self._updateStats(recvMsg)
                    elif recvMsg.msgType == DTM_MSG_ACK_RECEIVED_TASK:
                        self._updateStats(recvMsg)
                        self.loadBalancer.acked(recvMsg.senderWid, recvMsg.msg)
                    else:
                        _logger.warning("[%s] Unknown message type %s received will be ignored.", str(self.workerId), str(recvMsg.msgType))
                except Queue.Empty:
                    break


            if self.exitStatus.is_set():
                break

            currentNodeStatus = self._getLoadTuple()
            self.loadBalancer.updateSelfStatus(currentNodeStatus)

            sendUpdateList, sendTasksList = self.loadBalancer.takeDecision()
            self.tasksStatsLock.acquire()
            for sendInfo in sendTasksList:
                self.sendQueue.put(MessageContainer(msgType = DTM_MSG_TASK,
                                            senderWid = self.workerId,
                                            receiverWid = sendInfo[0],
                                            loadsDict = self.loadBalancer.getNodesDict(),
                                            targetsStats = self.tasksStats,
                                            prepTime = time.time(),
                                            sendTime = 0,
                                            ackNbr = sendInfo[2],
                                            msg = sendInfo[1]))

            for updateTo in sendUpdateList:
                self.sendQueue.put(DtmMessageContainer(msgType = DTM_MSG_REQUEST_TASK,
                                            senderWid = self.workerId,
                                            receiverWid = updateTo,
                                            loadsDict = self.loadBalancer.getNodesDict(),
                                            targetsStats = self.tasksStats,
                                            prepTime = time.time(),
                                            sendTime = 0,
                                            ackNbr = -1,
                                            msg = None))
            self.tasksStatsLock.release()
            self._startNewTask()
        return self._doCleanUp()


    def setOptions(self, *args, **kwargs):
        """
        Set a DTM global option.

        .. warning::
            This function must be called BEFORE ``start()``. It is also the user responsability to ensure that the same option is set on every worker.

        Currently, the supported options are :
            * **communicationManager** : can be *deap.dtm.mpi4py* (default) or *deap.dtm.commManagerTCP*.
            * **loadBalancer** : currently only the default *PDB* is available.
            * **printSummary** : if set, DTM will print a task execution summary at the end (mean execution time of each tasks, how many tasks did each worker do, ...)
            * **setTraceMode** : if set, will enable a special DTM tracemode. In this mode, DTM logs all its activity in XML files (one by worker). Mainly for DTM debug purpose, but can also be used for profiling.
            * **traceDir** : only available when setTraceMode is True. Path to the directory where DTM should save its log.
            * **taskGranularity** : set the granularity of the parallelism. It is specified in seconds, and represents the minimum amount of time to make a "task". If a task duration is smaller than this minimum, then DTM will try to combine two or more of those tasks to reach the wanted level of granularity. This can be very useful and may greatly reduce distribution overhead if some of your tasks are very small, or if you are working on a low-performance network. As on DTM 0.3, this only applies to synchronous calls (map, repeat, filter).

        This function can be called more than once. Any unknown parameter will have no effect.
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
            elif opt == "setTraceMode":
                self.traceMode = kwargs[opt]
            elif opt == "traceDir":
                self.traceDir = kwargs[opt]
            elif opt == "taskGranularity":
                self.serializeSmallTasks = True
                self.minGranularity = kwargs[opt]
            elif opt == "mapChunkSize":
                self.mapChunkSize = kwargs[opt]
            else:
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
            tmpImport = __import__(self.commManagerType, globals(), locals(), ['CommThread'], 0)
            if not hasattr(tmpImport, 'CommThread'):
                raise ImportError
            CommThread = tmpImport.CommThread
        except ImportError:
            _logger.warning("Warning : %s is not a suitable communication manager. Default to commManagerMpi4py.", self.commManagerType)
            tmpImport = __import__('deap.dtm.commManagerMpi4py', globals(), locals(), ['CommThread'], 0)
            CommThread = tmpImport.CommThread

        try:
            tmpImport = __import__(self.loadBalancerType, globals(), locals(), ['LoadBalancer'], 0)
            if not hasattr(tmpImport, 'LoadBalancer'):
                raise ImportError
            LoadBalancer = tmpImport.LoadBalancer
        except ImportError:
            _logger.warning("Warning : %s is not a suitable load balancer. Default to loadBalancerPDB.", self.loadBalancerType)
            tmpImport = __import__('deap.dtm.loadBalancerPDB', globals(), locals(), ['LoadBalancer'], 0)
            LoadBalancer = tmpImport.LoadBalancer

        self.commThread = CommThread(self.recvQueue, self.sendQueue, self.runningFlag, self.commExitNotification, self.commReadyEvent, self.dtmRandom, sys.argv)

        self.commThread.start()
        self.refTime = self._calibrateExecTime()

        self.commReadyEvent.wait()
        if self.commExitNotification.is_set():
            sys.exit()
            

        if self.commThread.isLaunchProcess:
            sys.exit()

        self.poolSize = self.commThread.poolSize
        self.workerId = self.commThread.workerId

        self.idGenerator = TaskIdGenerator(self.workerId)

        self.loadBalancer = LoadBalancer(self.commThread.iterOverIDs(), self.workerId, self.execQueue, self.dtmRandom)


        if self.traceMode:
            self.traceLock.acquire()
            self.traceRoot = etree.Element("dtm", {"version" : str(0.8), "workerId" : str(self.workerId), "poolSize" : repr(self.poolSize), "timeBegin" : repr(self.sTime), "benchmarkTime" : repr(self.refTime)})
            self.traceTasks = etree.SubElement(self.traceRoot, "tasksLog")
            self.traceLoadB = etree.SubElement(self.traceRoot, "loadBalancerLog")
            self.traceStats = etree.SubElement(self.traceRoot, "statsLog")
            self.traceComm = etree.SubElement(self.traceRoot, "commLog")
            self.traceLock.release()
            self.commThread.setTraceModeOn(self.traceComm)
            self.loadBalancer.setTraceModeOn(self.traceLoadB)

        if self.commThread.isRootWorker:

            if self.traceMode:
                # Create the log folder

                try:
                    os.mkdir(self.traceDir)
                except OSError:
                    _logger.warning("Log folder '" + self.traceDir + "' already exists!")


            _logger.info("DTM started with %i workers", self.poolSize)
            _logger.info("DTM load balancer is %s, and communication manager is %s", self.loadBalancerType, self.commManagerType)
            if self.traceMode:
                _logger.info("DTM tracing mode on")

            initTask = TaskContainer(tid = self.idGenerator.tid,
                                    creatorWid = self.workerId,
                                    creatorTid = None,
                                    taskIndex = [0],
                                    taskRoute = [self.workerId],
                                    creationTime = time.time(),
                                    target = [initialTarget],
                                    args = [args],
                                    kwargs = [kwargs],
                                    threadObject = None,
                                    taskState = DTM_TASK_STATE_IDLE,
                                    lastSubTaskDone = None)
            self.execQueue.put(initTask)

        return self._main()



    # The following methods are NOT called by the control thread, but by the EXECUTION THREADS
    # All the non-local objects used MUST be thread-safe

    def map(self, function, *iterables, **kwargs):
        """
        A parallel equivalent of the :func:`map` built-in function. It blocks till the result is ready.
        This method chops the iterables into a number of chunks determined by DTM in order to get the most efficient use of the workers.
        It takes any number of iterables (though it will shrink all of them to the length of the smallest one), and any others kwargs that will be
        transmitted as is to the *function* target.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid

        zipIterable = zip(*iterables)

        listResults = [None] * len(zipIterable)
        listTasks = []
        listTids = []

        chunkSize = self._getChunkSize(function)

        for indexBegin in xrange(0, len(zipIterable), chunkSize):
            topBound =  indexBegin+chunkSize if  indexBegin+chunkSize <= len(zipIterable) else len(zipIterable)
            task = TaskContainer(tid = self.idGenerator.tid,
                                    creatorWid = self.workerId,
                                    creatorTid = currentId,
                                    taskIndex = [i for i in xrange(indexBegin, topBound)],
                                    taskRoute = [],
                                    creationTime = time.time(),
                                    target = [function for i in xrange(indexBegin, topBound)],
                                    args = [zipIterable[i] for i in xrange(indexBegin, topBound)],
                                    kwargs = [kwargs for i in xrange(indexBegin, topBound)],
                                    threadObject = None,
                                    taskState = DTM_TASK_STATE_IDLE,
                                    lastSubTaskDone = None)
            listTasks.append(task)
            listTids.append(task.tid)

        if len(listTids) == 0:
            return []

        if self.traceMode:
            self.traceLock.acquire()
            newTaskElem = etree.SubElement(cThread.xmlTrace, "event",
                                           {"type" : "map",
                                            "time" : repr(time.time()),
                                            "target" : str(function.__name__),
                                            "childTasks" : str(listTids)[1:-1]})
            self.traceLock.release()

        self.waitingThreadsLock.acquire()
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = WaitInfoContainer(threadObject = cThread,
                                                    eventObject = cThread.waitingFlag,
                                                    waitBeginningTime = 0,
                                                    tasksWaitingCount = 0,
                                                    waitingMode = DTM_WAIT_NONE,
                                                    rWaitingDict = {})

        resultKey = listTids[0]
        self.waitingThreads[currentId].rWaitingDict[resultKey] = ExceptedResultContainer(tids = listTids,
                                waitingOn = True,
                                finished = False,
                                success = False,
                                callbackClass = None,
                                result = listResults)

        self.waitingThreads[currentId].tasksWaitingCount += len(listTasks)
        self.waitingThreads[currentId].waitingMode = DTM_WAIT_ALL


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


    def map_async(self, function, *iterables, **kwargs):
        """
        A non-blocking variant of the :func:`~deap.dtm.taskmanager.Control.map` method which returns a :class:`~deap.dtm.taskmanager.AsyncResult` object.
        It takes any number of iterables (though it will shrink all of them to the length of the smallest one), and any others kwargs that will be
        transmitted as is to the *function* target.

        .. note::
            A callback argument is not implemented, since it would make DTM
            unable to dispatch tasks and handle messages while it executes.
        """

        cThread = threading.currentThread()
        currentId = cThread.tid

        zipIterable = zip(*iterables)

        listResults = [None] * len(zipIterable)
        listTasks = []
        listTids = []

        chunkSize = self._getChunkSize(function)

        for indexBegin in xrange(0, len(zipIterable), chunkSize):
            topBound =  indexBegin+chunkSize if  indexBegin+chunkSize <= len(zipIterable) else len(zipIterable)
            task = TaskContainer(tid = self.idGenerator.tid,
                                    creatorWid = self.workerId,
                                    creatorTid = currentId,
                                    taskIndex = [i for i in xrange(indexBegin, topBound)],
                                    taskRoute = [],
                                    creationTime = time.time(),
                                    target = [function for i in xrange(indexBegin, topBound)],
                                    args = [zipIterable[i] for i in xrange(indexBegin, topBound)],
                                    kwargs = [kwargs for i in xrange(indexBegin, topBound)],
                                    threadObject = None,
                                    taskState = DTM_TASK_STATE_IDLE,
                                    lastSubTaskDone = None)

            listTasks.append(task)
            listTids.append(task.tid)

        if len(listTids) == 0:
            return []

        resultKey = listTids[0]

        if self.traceMode:
            newTaskElem = etree.SubElement(cThread.xmlTrace, "event",
                                           {"type" : "map_async",
                                            "time" : repr(time.time()),
                                            "target" : str(function.__name__),
                                            "childTasks" : str(listTids)[1:-1]})

        self.waitingThreadsLock.acquire()

        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = WaitInfoContainer(threadObject = cThread,
                                                    eventObject = cThread.waitingFlag,
                                                    waitBeginningTime = 0,
                                                    tasksWaitingCount = 0,
                                                    waitingMode = DTM_WAIT_NONE,
                                                    rWaitingDict = {})

        self.waitingThreads[currentId].rWaitingDict[resultKey] = ExceptedResultContainer(tids = listTids,
                                waitingOn = False,
                                finished = False,
                                success = False,
                                callbackClass = None,
                                result = listResults)

        self.waitingThreads[currentId].waitingMode = DTM_WAIT_NONE

        asyncRequest = AsyncResult(self, self.waitingThreads[currentId], resultKey, True)
        self.waitingThreads[currentId].rWaitingDict[resultKey].callbackClass = asyncRequest
        self.waitingThreadsLock.release()

        self.execQueue.putList(listTasks)

        self.runningFlag.set()

        return asyncRequest


    def apply(self, function, *args, **kwargs):
        """
        Equivalent of the :func:`apply` built-in function.
        It blocks till the result is ready. Given this blocks,
        :func:`~deap.dtm.taskmanager.Control.apply_async()` is better suited
        for performing work in parallel. Additionally, the passed in function
        is only executed in one of the workers of the pool.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid

        task = TaskContainer(tid = self.idGenerator.tid,
                                    creatorWid = self.workerId,
                                    creatorTid = currentId,
                                    taskIndex = [0],
                                    taskRoute = [],
                                    creationTime = time.time(),
                                    target = [function],
                                    args = [args],
                                    kwargs = [kwargs],
                                    threadObject = None,
                                    taskState = DTM_TASK_STATE_IDLE,
                                    lastSubTaskDone = None)

        if self.traceMode:
            newTaskElem = etree.SubElement(cThread.xmlTrace, "event",
                                           {"type" : "apply",
                                            "time" : repr(time.time()),
                                            "target" : str(function.__name__),
                                            "childTasks" : str([task.tid])[1:-1]})

        self.waitingThreadsLock.acquire()
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = WaitInfoContainer(threadObject = cThread,
                                                    eventObject = cThread.waitingFlag,
                                                    waitBeginningTime = 0,
                                                    tasksWaitingCount = 0,
                                                    waitingMode = DTM_WAIT_NONE,
                                                    rWaitingDict = {})

        resultKey = task.tid

        self.waitingThreads[currentId].rWaitingDict[resultKey] = ExceptedResultContainer(tids = [task.tid],
                                waitingOn = True,
                                finished = False,
                                success = False,
                                callbackClass = None,
                                result = [None])

        self.waitingThreads[currentId].tasksWaitingCount += 1
        self.waitingThreads[currentId].waitingMode = DTM_WAIT_ALL

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

    def apply_async(self, function, *args, **kwargs):
        """
        A non-blocking variant of the
        :func:`~deap.dtm.taskmanager.Control.apply` method which returns a
        :class:`~deap.dtm.taskmanager.AsyncResult` object.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid

        task = TaskContainer(tid = self.idGenerator.tid,
                                    creatorWid = self.workerId,
                                    creatorTid = currentId,
                                    taskIndex = [0],
                                    taskRoute = [],
                                    creationTime = time.time(),
                                    target = [function],
                                    args = [args],
                                    kwargs = [kwargs],
                                    threadObject = None,
                                    taskState = DTM_TASK_STATE_IDLE,
                                    lastSubTaskDone = None)

        if self.traceMode:
            newTaskElem = etree.SubElement(cThread.xmlTrace, "event",
                                           {"type" : "apply_async",
                                            "time" : repr(time.time()),
                                            "target" : str(function.__name__),
                                            "childTasks" : str([task.tid])[1:-1]})

        self.waitingThreadsLock.acquire()
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = WaitInfoContainer(threadObject = cThread,
                                                    eventObject = cThread.waitingFlag,
                                                    waitBeginningTime = 0,
                                                    tasksWaitingCount = 0,
                                                    waitingMode = DTM_WAIT_NONE,
                                                    rWaitingDict = {})

        resultKey = task.tid

        self.waitingThreads[currentId].rWaitingDict[resultKey] = ExceptedResultContainer(tids = [task.tid],
                                waitingOn = False,
                                finished = False,
                                success = False,
                                callbackClass = None,
                                result = [None])

        self.waitingThreads[currentId].waitingMode = DTM_WAIT_NONE

        asyncRequest = AsyncResult(self, self.waitingThreads[currentId], resultKey, False)
        self.waitingThreads[currentId].rWaitingDict[resultKey].callbackClass = asyncRequest
        self.waitingThreadsLock.release()

        self.execQueue.put(task)

        self.runningFlag.set()
        return asyncRequest

    def imap(self, function, *iterables):
        """
        An equivalent of :func:`itertools.imap`.

        This function creates an iterator which return results of the map
        operation, in order. One of the main benefits of this function against
        the traditionnal map function is that the first result may be yielded
        even if the computation of the others is not finished.
        """
        currentIndex = 0

        zipIterable = zip(*iterables)

        asyncResults = [self.apply_async(function, *zipIterable[i]) for i in xrange(len(zipIterable))]

        for result in asyncResults:
            yield result.get()



    def imap_unordered(self, function, iterable, chunksize=1):
        """
        An equivalent of :func:`itertools.imap`, but returning the results in
        an arbitrary order. It launchs *chunksize* tasks, and wait for the
        completion of one the them. It then yields the result of the first
        completed task : therefore, the return order can be predicted only if
        you use no more than one worker or if chunksize = 1.

        In return, as this function manages to have always *chunksize* tasks
        launched, it may speed up the evaluation when the execution times are
        very different. In this case, one should put a relatively large value
        of chunksize.
        """
        currentIndex = 0
        currentAsyncTasks = []
        countDataDone = 0

        while currentIndex < len(iterable) or len(currentAsyncTasks) > 0:
            while len(currentAsyncTasks) < chunksize and currentIndex < len(iterable):
                currentAsyncTasks.append(self.apply_async(function, iterable[currentIndex]))
                currentIndex += 1

            indexDone = currentAsyncTasks.index(self.waitAny(currentAsyncTasks))
            dataDone = currentAsyncTasks.pop(indexDone)
            yield dataDone.get()


    def filter(self, function, iterable):
        """
        Same behavior as the built-in :func:`filter`. The filtering is done
        localy, but the computation is distributed.
        """
        results = self.map(function, iterable)
        return [item for result, item in zip(results, iterable) if result]

    def repeat(self, function, n, *args, **kwargs):
        """
        Repeat the function *function* *n* times, with given args and keyworded args.
        Return a list containing the results.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid

        listResults = [None] * n
        listTasks = []
        listTids = []

        chunkSize = self._getChunkSize(function)

        for indexBegin in xrange(0, n, chunkSize):
            topBound =  indexBegin+chunkSize if  indexBegin+chunkSize <= n else n
            task = TaskContainer(tid = self.idGenerator.tid,
                                    creatorWid = self.workerId,
                                    creatorTid = currentId,
                                    taskIndex = [i for i in xrange(indexBegin, topBound)],
                                    taskRoute = [],
                                    creationTime = time.time(),
                                    target = [function for i in xrange(indexBegin, topBound)],
                                    args = [args for i in xrange(indexBegin, topBound)],
                                    kwargs = [kwargs for i in xrange(indexBegin, topBound)],
                                    threadObject = None,
                                    taskState = DTM_TASK_STATE_IDLE,
                                    lastSubTaskDone = None)
            listTasks.append(task)
            listTids.append(task.tid)

        self.waitingThreadsLock.acquire()
        if currentId not in self.waitingThreads.keys():
            self.waitingThreads[currentId] = WaitInfoContainer(threadObject = cThread,
                                                    eventObject = cThread.waitingFlag,
                                                    waitBeginningTime = 0,
                                                    tasksWaitingCount = 0,
                                                    waitingMode = DTM_WAIT_NONE,
                                                    rWaitingDict = {})

        resultKey = listTids[0]
        self.waitingThreads[currentId].rWaitingDict[resultKey] = ExceptedResultContainer(tids = listTids,
                                waitingOn = True,
                                finished = False,
                                success = False,
                                callbackClass = None,
                                result = listResults)

        self.waitingThreads[currentId].tasksWaitingCount += len(listTasks)
        self.waitingThreads[currentId].waitingMode = DTM_WAIT_ALL


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


    def waitAll(self, reqList = []):
        """
        Wait for all pending asynchronous results in list *reqList*. When this
        function returns, DTM guarantees that all ready() call those
        asynchronous tasks will return true.

        .. note::
            If *reqList* is not specified or an empty list, DTM will wait over
            all the current asynchronous tasks.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid

        idsToBlock = [asyncReq.taskKey for asyncReq in reqList]

        self.waitingThreadsLock.acquire()
        if currentId not in self.waitingThreads.keys() or len(self.waitingThreads[currentId].rWaitingDict) == 0:
            self.waitingThreadsLock.release()
            return

        mustWait = False
        for wChildTaskKey in self.waitingThreads[currentId].rWaitingDict:
            if len(idsToBlock) == 0 or wChildTaskKey in idsToBlock:
                self.waitingThreads[currentId].rWaitingDict[wChildTaskKey].waitingOn = True
                mustWait = True

        if mustWait:
            self.waitingThreads[currentId].waitingMode = DTM_WAIT_ALL
            self.waitingThreadsQueue.put(threading.currentThread().taskInfo)
            self.waitingThreadsLock.release()
            cThread.waitForResult()
        else:
            self.waitingThreadsLock.release()


    def waitAny(self, reqList = []):
        """
        Wait for any pending asynchronous tasks in list *reqList*, then
        return the :class:`~deap.dtm.taskmanager.AsyncResult` object of the
        last finished asynchronous task (say, the most recent one). If there
        is no pending asynchronous tasks, this function will return None.

        .. note::
            If *reqList* is not specified or an empty list, DTM will wait over
            any of the current asynchronous tasks.

        .. warning::
            This function only guarantees that at least one of the asynchronous
            task will be done when it returns, but actually many others may
            have been done. In this case, this function returns only the last
            one, even if called more than once.
        """
        cThread = threading.currentThread()
        currentId = cThread.tid

        idsToBlock = [asyncReq.taskKey for asyncReq in reqList]

        self.waitingThreadsLock.acquire()
        if currentId not in self.waitingThreads.keys() or len(self.waitingThreads[currentId].rWaitingDict) == 0:
            self.waitingThreadsLock.release()
            if len(reqList) > 0:
                return reqList[0]
            else:
                return None

        mustWait = False
        for wChildTaskKey in self.waitingThreads[currentId].rWaitingDict:
            if len(idsToBlock) == 0 or wChildTaskKey in idsToBlock:
                self.waitingThreads[currentId].rWaitingDict[wChildTaskKey].waitingOn = True
                mustWait = True

        if mustWait:
            self.waitingThreads[currentId].waitingMode = DTM_WAIT_ANY
            self.waitingThreadsQueue.put(threading.currentThread().taskInfo)
            self.waitingThreadsLock.release()
            cThread.waitForResult()
            return cThread.taskInfo.lastSubTaskDone
        else:
            self.waitingThreadsLock.release()
            if len(reqList) > 0:
                return reqList[0]
            else:
                return None

    def testAll(self, reqList = []):
        """
        Check whether all pending asynchronous tasks in list *reqList* are
        done. It does not lock if it is not the case, but returns False.

        .. note::
            If *reqList* is not specified or an empty list, DTM will test the
            completion of all the current asynchronous tasks.
        """
        threadId = threading.currentThread().tid
        idsToTest = [asyncReq.taskKey for asyncReq in reqList]

        self.waitingThreadsLock.acquire()

        if threadId in self.waitingThreads:
            for wChildTaskKey in self.waitingThreads[threadId].rWaitingDict:
                if len(idsToTest) == 0 or wChildTaskKey in idsToTest:
                    self.waitingThreadsLock.release()
                    return False

        self.waitingThreadsLock.release()
        return True


    def testAny(self, reqList = []):
        """
        Test the completion of any pending asynchronous task in list *reqList*,
        then return the :class:`~deap.dtm.taskmanager.AsyncResult` object of
        the last finished asynchronous task (say, the most recent one). If
        there is no pending asynchronous tasks, this function will return None.

        .. note::
            If *reqList* is not specified or an empty list, DTM will test the
            completion of any of the current asynchronous tasks.

        .. warning::
            This function always returns the same task (the last) if called
            more than once with the same parameters (i.e. it does not delete
            the state of a completed task when called, so a second call will
            produce the same output). It is the user responsability to
            provide a *reqList* containing only the tasks which he does not
            know whether they are completed or not.
            Similarly, multiple calls without specifing the *reqList* param
            will always return the last finished asynchronous task.
        """

        cThread = threading.currentThread()
        threadId = threading.currentThread().tid
        idsToTest = [asyncReq.taskKey for asyncReq in reqList]

        allDone = True
        for idT in idsToTest:
            if idT not in cThread.asyncTasksDoneList:
                allDone = False
                break

        if allDone and len(reqList) > 0:
            return reqList[0]

        if len(idsToTest) == 0:
            if len(cThread.asyncTasksDoneList) == 0:
                return None
            else:
                return cThread.taskInfo.lastSubTaskDone     # Will be None if no task
        else:
            for i,idT in enumerate(idsToTest):
                if idT in cThread.asyncTasksDoneList:
                    return reqList[i]
            return None

    def getWorkerId(self):
        """
        Return a unique ID for the current worker. Depending of the
        communication manager type, it can be virtually any Python
        immutable type.

        .. note::
            With MPI, the value returned is the MPI slot number.
        """
        return self.workerId




class DtmThread(threading.Thread):
    """
    DTM execution threads. Those are one of the main parts of DTM.
    They should not be created or called directly by the user.
    """
    def __init__(self, structInfo, controlThread, xmlTrace=None):
        threading.Thread.__init__(self)

        self.taskInfo = structInfo      # TaskContainer

        self.taskInfo.threadObject = self   # Remind that we are the exec thread

        self.tid = structInfo.tid
        self.t = structInfo.target
        self.control = controlThread

        self.spawnedTasks = False

        self.waitingFlag = threading.Event()
        self.waitingFlag.clear()

        self.asyncTasksDoneList = []        # IDs of async tasks done

        self.timeExec = 0
        self.timeBegin = 0
        if structInfo.creatorTid is None:
            self.isRootTask = True
        else:
            self.isRootTask = False

        self.xmlTrace = xmlTrace

    def run(self):
        # The lock is already acquired for us
        self.taskInfo.taskState = DTM_TASK_STATE_RUNNING
        returnedValues = [None for i in xrange(len(self.taskInfo.target))]
        success = [True for i in xrange(len(self.taskInfo.target))]
        if not self.xmlTrace is None:
            # Debug output in xml object
            self.control.traceLock.acquire()
            etree.SubElement(self.xmlTrace, "event", {"type" : "begin", "worker" : str(self.control.workerId), "time" : repr(time.time())})
            self.control.traceLock.release()

        totalTime = 0
        for subtaskIndex in xrange(len(self.taskInfo.target)):
            self.timeBegin = time.time()
            self.timeExec = 0

            try:
                returnedValues[subtaskIndex] = self.taskInfo.target[subtaskIndex](*(self.taskInfo.args[subtaskIndex]), **(self.taskInfo.kwargs[subtaskIndex]))
            except Exception as expc:
                returnedValues = expc
                strWarn = "An exception of type " + str(type(expc)) + " occured on worker " + str(self.control.workerId) + " while processing task " + str(self.tid)
                _logger.warning(strWarn)
                _logger.warning("This will be transfered to the parent task.")
                _logger.warning("Exception traceback (most recent call last) :\n")
                traceExcep = traceback.format_exc().split("\n")
                if len(traceExcep) > 3:
                    # We do not want to see the DTM call to the target in the trace
                    for l in traceExcep[3:]:
                        print(l)
                else:
                    # An error in DTM itself?
                    for l in traceExcep:
                        print(l)

                success[subtaskIndex] = False
                break       # Is it really what do we want? Stop on every exception?

            self.timeExec += time.time() - self.timeBegin
            totalTime += self.timeExec

            if success[subtaskIndex]:
                spawnedBool = self.spawnedTasks or len(self.asyncTasksDoneList) > 0
                try:
                    self.control._addTaskStat(self.taskInfo.target[subtaskIndex].__name__, self.timeExec, spawnedBool)
                except AttributeError:
                    self.control._addTaskStat(str(self.taskInfo.target[subtaskIndex]), self.timeExec, spawnedBool)

        self.control.dtmExecLock.release()


        if not self.xmlTrace is None:
            # Debug output in xml object
            self.control.traceLock.acquire()
            etree.SubElement(self.xmlTrace, "event", {"type" : "end", "worker" : str(self.control.workerId), "time" : repr(time.time()), "execTime" : repr(totalTime), "success" : str(success)[1:-1]})
            self.control.traceLock.release()


        if self.isRootTask:
            # Is this task the root task (launch by dtm.start)? If so, we quit
            self.control.lastRetValue = (success[0], returnedValues)
            self.control.exitSetHere = True
            self.control.exitStatus.set()
        else:
            # Else, tell the communication thread to return the result
            resultStruct = ResultContainer(tid = self.tid,
                                            parentTid = self.taskInfo.creatorTid,
                                            taskIndex = self.taskInfo.taskIndex,
                                            execTime = totalTime,
                                            success = success,
                                            result = returnedValues)

            self.control._returnResult(self.taskInfo.creatorWid, resultStruct)

        # Tell the control thread that something happened
        self.control._startNewTask()

        if self.isRootTask:
            self.control.runningFlag.set()

        self.control.waitingThreadsLock.acquire()
        if self.tid in self.control.waitingThreads.keys():
            del self.control.waitingThreads[self.tid]
        self.control.waitingThreadsLock.release()
        self.taskInfo.taskState = DTM_TASK_STATE_FINISH


    def waitForResult(self):
        # Clear the execution lock, and sleep
        beginTimeWait = time.time()
        self.timeExec += beginTimeWait - self.timeBegin
        self.control.dtmExecLock.release()
        self.spawnedTasks = True
        self.taskInfo.taskState = DTM_TASK_STATE_WAITING

        if not self.xmlTrace is None:
            # Debug output in xml object
            self.control.traceLock.acquire()
            etree.SubElement(self.xmlTrace, "event", {"type" : "sleep", "worker" : str(self.control.workerId), "time" : repr(beginTimeWait)})
            self.control.traceLock.release()

        self.control._startNewTask()
        self.control.runningFlag.set()

        self.waitingFlag.wait()
        self.waitingFlag.clear()

        # At this point, we already have acquired the execution lock
        self.taskInfo.taskState = DTM_TASK_STATE_RUNNING
        self.timeBegin = time.time()

        if not self.xmlTrace is None:
            # Debug output in xml object
            self.control.traceLock.acquire()
            etree.SubElement(self.xmlTrace, "event", {"type" : "wakeUp", "worker" : str(self.control.workerId), "time" : repr(self.timeBegin)})
            self.control.traceLock.release()



class AsyncResult(object):
    """
    The class of the result returned by :func:`~deap.dtm.taskmanager.Control.map_async()` and :func:`~deap.dtm.taskmanager.Control.apply_async()`.
    """
    def __init__(self, control, waitingInfo, taskKey, resultIsIterable):
        self.control = control
        self.resultReturned = False
        self.resultSuccess = False
        self.resultVal = None
        self.taskKey = taskKey
        self.dictWaitingInfo = waitingInfo
        self.isIter = resultIsIterable


    def _dtmCallback(self):
        """
        Used by DTM to inform the object that the job is done
        Should not be called by users
        """
        self.resultSuccess = self.dictWaitingInfo.rWaitingDict[self.taskKey].success
        self.resultVal = self.dictWaitingInfo.rWaitingDict[self.taskKey].result
        self.resultReturned = True

        del self.dictWaitingInfo.rWaitingDict[self.taskKey]


    def get(self):
        """
        Return the result when it arrives. If an exception has been raised in
        the child task (and thus catched by DTM), then it will be raised when
        this method will be called.

        .. note::
            This is a blocking call : caller will wait in this function until the result is ready.
            To check for the avaibility of the result, use :func:`~deap.dtm.taskmanager.AsyncResult.ready()`.
        """
        if not self.resultReturned:
            self.wait()

        if self.resultSuccess:
            if self.isIter:
                return self.resultVal
            else:
                return self.resultVal[0]
        else:
            raise self.resultVal

    def wait(self):
        """
        Wait until the result is available. When this function returns, DTM
        guarantees that a call to
        :func:`~deap.dtm.taskmanager.AsyncResult.ready()` will return true.
        """

        self.control.waitingThreadsLock.acquire()

        if self.ready():
            # This test MUST be protected by the mutex on waitingThreads
            self.control.waitingThreadsLock.release()
            return

        self.control.waitingThreads[threading.currentThread().tid].waitingMode = DTM_WAIT_ALL
        self.control.waitingThreads[threading.currentThread().tid].rWaitingDict[self.taskKey].waitingOn = True
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
            raise AssertionError("Call AsyncResult.successful() before the results were ready!")
        return self.resultSuccess
