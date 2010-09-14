import threading
import time
import random
import Queue


# Constantes
DTM_MPI_LATENCY = 0.1
DTM_CONTROL_THREAD_LATENCY = 0.01
DTM_ASK_FOR_TASK_DELAY = 0.5


MSG_COMM_TYPE = 0
MSG_SENDER_INFO = 1
MSG_NODES_INFOS = 2


# Lock d'execution global qui assure qu'un seul thread a la fois
# essaie de s'executer
# Il permet aussi de savoir au thread de controle si on execute encore quelque chose
dtmGlobalExecutionLock = threading.Lock()


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

class DtmControl(object):
    """
    DtmControl is the main DTM class. The dtm object you receive when you use ``from dtm.taskmanager import dtm``
    is an instance of this class.

    Most of its methods are used by your program, in the execution tasks; however, two of thems (start() and setOptions()) MUST be called
    in the MainThread (i.e. the thread started by the Python interpreter).

    As this class is instancied directly in the module, initializer takes no arguments.
    """
    def __init__(self):
        self.sTime = time.time()

        self.waitingThreads = {}
        self.waitingThreadsLock = threading.Lock()

        self.asyncWaitingList = {}
        self.asyncWaitingListLock = threading.Lock()

        self.tasksStatsLock = threading.Lock()
        self.tasksStats = {}

        self.waitingForRestartQueue = Queue.Queue()
        self.execQueue = Queue.Queue()

        self.recvQueue = Queue.Queue()
        self.sendQueue = Queue.Queue()

        self.exitStatus = threading.Event()

        self.commExitNotification = threading.Event()

        self.commReadyEvent = threading.Event()

        self.exitState = (None, None)
        self.exitSetHere = False

        self.commManagerType = "pympi"
        self.isStarted = False



    def _doCleanUp(self):
        """
        Clean up function, called at this end of the execution.
        Should NOT be called by the user.
        """

        msgT = "Rank " + str(self.workerId) + " ("+str(threading.currentThread().name)+" / " + str(threading.currentThread().ident) + ")\n"
        for target,times in self.tasksStats.items():
            msgT += "\t" + str(target) + " : Avg=" + str(sum(times)/float(len(times))) + ", Min=" + str(min(times)) + ", Max=" + str(max(times)) + ", Total : " + str(sum(times)) + " used by " + str(len(times)) + " calls\n"
        msgT += "\n"
        _printDtmMsg(msgT)

        if self.exitSetHere:
            for n in xrange(self.poolSize):
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
            _printDtmMsg("Total execution time : " + str(time.time() - self.sTime))



    def _returnResult(self, idToReturn, resultInfo):
        """
        Called by the execution threads when they have to return a result
        Should NOT be called explicitly by the user
        """
        if idToReturn == self.workerId:
            self._dispatchResult(resultInfo)
        else:
            self.sendQueue.put((idToReturn, ("Result", self.workerId, self.nodesStatus, resultInfo)))

    def _updateNodesDict(self, fromNodeNumber, newDict):
        """
        Called by the control thread to update its dictionnary
        Should NOT be called explicitly by the user
        """
        for i in xrange(len(newDict)):
            if (i == fromNodeNumber or newDict[i][3] > self.nodesStatus[i][3]) and i != self.workerId:
                self.nodesStatus[i] = newDict[i]

    def _askForTask(self):
        """
        Called by the control thread, to ask the other workers for tasks
        Should NOT be called explicitly by the user
        """
        curTime = time.time()
        listNodesWorking = [i for i,n in self.nodesStatus.items() if n[0] > 0 and i != self.workerId and curTime - n[4] > DTM_ASK_FOR_TASK_DELAY]
        for nodeId in listNodesWorking:
            self.sendQueue.put((nodeId, ("RequestTask", self.workerId, self.nodesStatus, time.time())))
            self.nodesStatus[nodeId][4] = curTime

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

            for listAsync in self.asyncWaitingList.values():
                if tidParent in listAsync:
                    conditionLock.acquire()
                    conditionLock.notifyAll()
                    conditionLock.release()
                    self.waitingThreadsLock.release()
                    return

            self.waitingForRestartQueue.put(conditionLock)

        self.waitingThreadsLock.release()

    def _main(self):
        """
        Main loop of the control thread
        Should NOT be called explicitly by the user
        """

        while True:

            while True:
                try:
                    recvMsg = self.recvQueue.get_nowait()
                    if recvMsg[MSG_COMM_TYPE] == "Exit":
                        self.exitStatus.set()
                        self.exitState = (recvMsg[2], recvMsg[3])
                        break
                    elif recvMsg[MSG_COMM_TYPE] == "Task":
                        self._updateNodesDict(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                        for taskData in recvMsg[4]:
                            taskData[4].append(self.workerId)
                            self.execQueue.put(taskData)
                    elif recvMsg[MSG_COMM_TYPE] == "RequestTask":
                        self._updateNodesDict(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                    elif recvMsg[MSG_COMM_TYPE] == "Result":
                        self._updateNodesDict(recvMsg[MSG_SENDER_INFO], recvMsg[MSG_NODES_INFOS])
                        self._dispatchResult(recvMsg[3])
                    else:
                        print("DTM warning : unknown message type ("+str(recvMsg[MSG_COMM_TYPE])+") received will be ignored.")
                except Queue.Empty:
                    break

            if self.exitStatus.is_set():
                break

            self.nodesStatus[self.workerId] = [self.execQueue.qsize(), self.waitingForRestartQueue.qsize(), len(self.waitingThreads), time.time(), time.time()]


            availableNodes = [i for i,n in self.nodesStatus.items() if n[0] <= 5 and n[0] < self.nodesStatus[self.workerId][0] and i != self.workerId]

            if self.nodesStatus[self.workerId][0] > 1 and len(availableNodes) > 0:
                chosenSlot = random.choice(availableNodes)

                nbrTask = self.execQueue.qsize() / self.poolSize
                if nbrTask == 0:
                    nbrTask = 1

                try:
                    taskList = []
                    try:
                        for t in xrange(nbrTask):
                            taskList.append(self.execQueue.get_nowait())
                    except Queue.Empty:
                        if len(taskList) == 0:
                            raise Queue.Empty
                        else:
                            pass

                    nbrTask = len(taskList)
                    self.sendQueue.put((chosenSlot, ("Task", self.workerId, self.nodesStatus, nbrTask, taskList)))
                    self.nodesStatus[chosenSlot][0] += nbrTask
                except Queue.Empty:
                    pass

            if dtmGlobalExecutionLock.acquire(False):
                dtmGlobalExecutionLock.release()

                try:
                    wTaskLock = self.waitingForRestartQueue.get_nowait()
                    wTaskLock.acquire()
                    wTaskLock.notifyAll()
                    wTaskLock.release()
                    continue
                except Queue.Empty:
                    pass

                try:
                    newTask = self.execQueue.get_nowait()
                    newThread = DtmThread(tid=newTask[0], returnInfo=(newTask[1],newTask[2],newTask[3]), target=newTask[6], args=newTask[7], kwargs=newTask[8], control=self)
                    newThread.start()

                    continue
                except Queue.Empty:
                    pass

                self._askForTask()

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


    def start(self, initialTarget):
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

        self.commThread.start()
        self.commReadyEvent.wait()

        self.poolSize = self.commThread.poolSize
        self.workerId = self.commThread.workerId

        self.idGenerator = DtmTaskIdGenerator(self.workerId)

        self.nodesStatus = {}
        for wId in self.commThread.iterOverIDs():
            self.nodesStatus[wId] = [0,0,0,time.time(), time.time()]
        
        if self.commThread.isRootWorker:
            _printDtmMsg("DTM started with " + str(self.poolSize) + " workers")
            initTask = (self.idGenerator.tid, None, None, None, [self.workerId], time.time(), initialTarget, (), {})
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
        conditionObject = threading.currentThread().waitingCondition

        listResults = [None] * len(iterable)

        self.waitingThreadsLock.acquire()
        for index,elem in enumerate(iterable):
            task = (self.idGenerator.tid, self.workerId, currentId, index, [self.workerId], time.time(), function, (elem,), {})
            listTid.append(task[0])
            self.execQueue.put(task)

        self.waitingThreads[currentId] = (conditionObject, listTid, time.time(), listResults)
        self.waitingThreadsLock.release()

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

        threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, target=function, args=iterable, control=self)
        asyncRequest = DtmAsyncResult(threadAsync, control=self)

        return asyncRequest


    def _apply(self, function, args, kwargs):
        """
        Special function that can be used on boot apply() and apply_async()
        Should not be called directly by the user, as apply() do almost the same job.
        """
        
        currentId = threading.currentThread().tid
        conditionObject = threading.currentThread().waitingCondition

        self.waitingThreadsLock.acquire()
        task = (self.idGenerator.tid, self.workerId, currentId, 0, [self.workerId], time.time(), function, args, kwargs)
        listTid = [task[0]]
        self.execQueue.put(task)
        self.waitingThreads[currentId] = (conditionObject, listTid, time.time(), [None])
        self.waitingThreadsLock.release()

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
        threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, target=function, args=args, kwargs=kwargs, control=self, areArgsIterable = False)
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
    def __init__(self, group=None, target=None, name=None, control=None, returnInfo = None, tid=None, args=(), kwargs={}):
        threading.Thread.__init__(self)
        
        self.tid = tid
        self.t = target
        self.control = control
        self.returnInfo = returnInfo
        self.waitingCondition = threading.Condition()
        self.argsL = args
        self.kwargsL = kwargs
        self.timeExec = 0
        self.timeBegin = 0
        if returnInfo[0] is None:
            self.isRootTask = True
        else:
            self.isRootTask = False

    def run(self):
        # On s'assure qu'aucun autre thread ne s'execute
        dtmGlobalExecutionLock.acquire()
        
        self.timeBegin = time.time()
        returnedR = self.t(*self.argsL, **self.kwargsL)
        self.timeExec += time.time() - self.timeBegin
        if self.isRootTask:
            # Si la tache racine est terminee alors on quitte
            self.control.exitSetHere = True
            self.control.exitStatus.set()
        else:
            # Sinon on retourne le resultat
            resultTuple = (self.tid, self.returnInfo[1], self.returnInfo[2], self.timeExec, returnedR)
            self.control._returnResult(self.returnInfo[0], resultTuple)

        # On met a jour le dictionnaire des charges
        self.control.tasksStatsLock.acquire()
        try:
            self.control.tasksStats.setdefault(self.t.__name__,[]).append(self.timeExec)
        except AttributeError:
            self.control.tasksStats.setdefault(self.t,[]).append(self.timeExec)
        self.control.tasksStatsLock.release()
        
        dtmGlobalExecutionLock.release()


    def waitForCondition(self):
        # Libere le lock d'execution et attend que la condition soit remplie pour continuer
        self.waitingCondition.acquire()
        
        beginTimeWait = time.time()
        self.timeExec += beginTimeWait - self.timeBegin
        dtmGlobalExecutionLock.release()
        
        self.waitingCondition.wait()
        self.waitingCondition.release()
        
        dtmGlobalExecutionLock.acquire()
        self.timeBegin = time.time()
        return time.time() - beginTimeWait


class DtmAsyncWaitingThread(threading.Thread):
    """
    Cette classe est semblable a DtmThread; elle sert de thread d'attente aux taches asynchrones
    (car le fonctionnement de DTM suppose que tout resultat est attendu par un thread et son lock conditionnel)
    Par ailleurs, elle notifie un objet special lorsque son resultat est arrive
    """
    def __init__(self, tid = None, target = None, args = (), kwargs = {}, areArgsIterable = True, control = None, returnToObj = None):
        threading.Thread.__init__(self)
        self.tid = tid
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.iterable = areArgsIterable
        self.control = control
        self.waitingCondition = threading.Condition()
        self.returnTo = returnToObj         # Cet objet doit avoir une methode _giveResult(resultat)

    def setObjToReturnTo(self, obj):
        self.returnTo = obj
    
    def run(self):
        if self.iterable:
            result = self.control.map(self.target, self.args)
        else:
            result = self.control._apply(self.target, self.args, self.kwargs)

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
            self.dtmInterface.waitingForRestartQueue.put(self.returnThread.waitingCondition)
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