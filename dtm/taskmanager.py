import threading
import time
import random
import Queue
import sys
from commManager import DtmCommThread

# Constantes
DTM_TAG_EXIT = 1
DTM_TAG_RETURN_TASK = 2
DTM_TAG_QUERY_TASK = 3
DTM_TAG_RETURN_RESULT = 4

DTM_MPI_LATENCY = 0.1
DTM_CONTROL_THREAD_LATENCY = 0.01
DTM_ASK_FOR_TASK_DELAY = 0.5


dtmGlobalExecutionLock = threading.Lock()


def _printDtmMsg(msg, gravity=1):
    print("#--------------- DTM ---------------#")
    print("# " + msg + "\n")


class DtmTaskIdGenerator(object):
    def __init__(self, rank, initId = 0):
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

    class __DtmControl:
        """
        Cette classe est le coeur de DTM. Elle est speciale au sens ou elle possede des methodes
        destinees aux threads d'execution, et d'autres destinees uniquement au thread principal
        start(), _main() et _doCleanUp() sont les methodes du thread principal (_main etant la boucle principale)
        Les autres methodes sont appelees (et executees dans) les threads d'EXECUTION
        """
        def __init__(self):
            self.sTime = time.time()

            self.waitingThreads = {}
            self.waitingThreadsLock = threading.Lock()

            self.asyncWaitingList = {}
            self.asyncWaitingListLock = threading.Lock()

            self.resultsLock = threading.Lock()
            self.results = {}

            self.tasksStatsLock = threading.Lock()
            self.tasksStats = {}



            # Queues d'execution
            self.waitingForRestartQueue = Queue.Queue()
            self.execQueue = Queue.Queue()

            # Queues partages
            self.recvQueue = Queue.Queue()
            self.sendQueue = Queue.Queue()


            self.currentExecThread = None

            self.exitStatus = threading.Event()
            self.commReadyEvent = threading.Event()

            self.exitState = (None, None)
            

            #self.updateReceiveThread.daemon = True
            self.commThread = DtmCommThread(self.recvQueue, self.sendQueue, self.exitStatus, self.commReadyEvent)

            self.poolSize = self.commThread.poolSize
            self.workerId = self.commThread.workerId

            self.idGenerator = DtmTaskIdGenerator(self.workerId)
            
            self.nodesStatus = [[0,0,0,time.time(), time.time()] for i in xrange(self.poolSize)]
            
            if self.commThread.isRootWorker:
                _printDtmMsg("DTM started with " + str(self.poolSize) + " workers")



        def _doCleanUp(self):
            """
            Fonction charge de faire le clean up a la fin
            """
            #if self.commThread.isRootWorker:
            msgT = "Rank " + str(self.workerId) + " ("+str(threading.currentThread().name)+" / " + str(threading.currentThread().ident) + ")\n"
            for target,times in self.tasksStats.items():
                try:
                    msgT += "\t" + str(target.__name__) + " : Avg=" + str(sum(times)/float(len(times))) + ", Min=" + str(min(times)) + ", Max=" + str(max(times)) + ", Total : " + str(sum(times)) + " used by " + str(len(times)) + " calls\n"
                except AttributeError:
                    msgT += "\t" + str(target) + " : Avg=" + str(sum(times)/float(len(times))) + ", Min=" + str(min(times)) + ", Max=" + str(max(times)) + ", Total : " + str(sum(times)) + " used by " + str(len(times)) + " calls\n"
            msgT += "\n"
            _printDtmMsg(msgT)

            if self.commThread.isRootWorker:
                for n in xrange(self.poolSize):
                    if n == self.workerId:
                        continue
                    self.sendQueue.put((n, ("Exit", self.workerId, 0, "Exit message")))

            self.commThread.join()

            del self.execQueue
            del self.sendQueue
            del self.recvQueue

            countThreads = sum([1 for th in threading.enumerate() if not th.daemon])
            if countThreads > 1:
                print("Warning : there's more than 1 active thread at the exit (" + str(threading.activeCount()) + " total)\n" + str(threading.enumerate()))

            #mpi.finalize()


        def _returnResult(self, idToReturn, resultInfo):
            if idToReturn == self.workerId:
                self._dispatchResult(resultInfo)
            else:
                self.sendQueue.put((idToReturn, ("Result", self.workerId, self.nodesStatus, resultInfo)))
        
        def _updateNodesDict(self, fromNodeNumber, newDict):
            for i in xrange(len(newDict)):
                if (i == fromNodeNumber or newDict[i][3] > self.nodesStatus[i][3]) and i != self.workerId:
                    self.nodesStatus[i] = newDict[i]

        def _askForTask(self):
            curTime = time.time()
            listNodesWorking = [i for i,n in enumerate(self.nodesStatus) if n[0] > 0 and i != self.workerId and curTime - n[4] > DTM_ASK_FOR_TASK_DELAY]
            for nodeId in listNodesWorking:
                self.sendQueue.put((nodeId, ("RequestTask", self.workerId, self.nodesStatus[:], time.time())))
                self.nodesStatus[nodeId][4] = curTime
        
        def _dispatchResult(self, result):
            tidParent = result[1]

            self.resultsLock.acquire()
            if result[2][0]:    # Le resultat est un iterable
                self.results[tidParent][result[2][1]] = result[4]
            else:
                self.results[tidParent] = result[4]
            self.resultsLock.release()

            self.waitingThreadsLock.acquire()

            self.waitingThreads[tidParent][1].remove(result[0])
            if len(self.waitingThreads[tidParent][1]) == 0:      # Tous les resultats sont arrives
                conditionLock = self.waitingThreads[tidParent][0]
                del self.waitingThreads[tidParent]              # On supprime la tache d'attente
                self.waitingForRestartQueue.put(conditionLock)

            self.waitingThreadsLock.release()

        def _main(self):
            while True:
                # On update notre etat
                self.nodesStatus[self.workerId] = [self.execQueue.qsize(), self.waitingForRestartQueue.qsize(), len(self.waitingThreads), time.time(), time.time()]
                #if mpi.rank == 0:
                    #print("Status updated")
                # On verifie les messages recus
                while True:
                    try:
                        recvMsg = self.recvQueue.get_nowait()
                        #if mpi.rank == 0:
                            #print("Receive from " + str(recvMsg[1]))
                        if recvMsg[0] == "Exit":
                            self.exitStatus.set()
                            self.exitState = (recvMsg[2], recvMsg[3])
                            break
                        elif recvMsg[0] == "Task":
                            self._updateNodesDict(recvMsg[1], recvMsg[2])
                            for taskData in recvMsg[4]:
                                taskData[4].append(self.workerId)
                                self.execQueue.put(taskData)
                        elif recvMsg[0] == "RequestTask":
                            self._updateNodesDict(recvMsg[1], recvMsg[2])
                        elif recvMsg[0] == "Result":
                            self._updateNodesDict(recvMsg[1], recvMsg[2])
                            self._dispatchResult(recvMsg[3])
                        else:
                            print("DTM warning : unknown message type ("+str(recvMsg[0])+") received will be ignored.")
                    except Queue.Empty:
                        break
                    
                if self.exitStatus.is_set():
                    break
                    
                # On determine si on doit envoyer des taches
                availableNodes = [i for i,n in enumerate(self.nodesStatus) if n[0] <= 5 and n[0] < self.nodesStatus[self.workerId][0] and i != self.workerId]

                if self.nodesStatus[self.workerId][0] > 1 and len(availableNodes) > 0:
                    # Cool il y a un slot de libre
                    chosenSlot = random.choice(availableNodes)

                    # On essaie de dispatcher equitablement les taches
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
                                raise Queue.Empty       # Si on a aucune tache a envoyer, on va au prochain catch
                            else:
                                pass                    # Sinon, on envoie ce qu'on peut

                        # On lui envoie la tache
                        nbrTask = len(taskList)
                        self.sendQueue.put((chosenSlot, ("Task", self.workerId, self.nodesStatus[:], nbrTask, taskList)))

                        #On peut supposer que le noeud aura maintenant 'nbrTask' taches de plus dans son execQ
                        self.nodesStatus[chosenSlot][0] += nbrTask
                    except Queue.Empty: # On a rien a lui donner
                        pass
                
                # Si on est deja en train d'executer un thread, ca ne sert a rien d'en ajouter un
                # Mieux vaut le laisser dans la execQueue, et peut-etre qu'un autre node libre
                # pourra le demander et l'executer avant nous
                if dtmGlobalExecutionLock.acquire(False):    # On verifie deja si on est en train de faire quelque chose
                    dtmGlobalExecutionLock.release()

                    try:
                        # On redemarre en priorite les taches en attente (qui ont recu leurs resultats)
                        wTaskLock = self.waitingForRestartQueue.get_nowait()
                        wTaskLock.acquire()
                        wTaskLock.notifyAll()
                        wTaskLock.release()

                        # On laisse au thread le temps de reprendre le lock global d'execution
                        #time.sleep(0.001)
                        continue
                    except Queue.Empty:
                        pass

                    try:
                        newTask = self.execQueue.get_nowait()

                        newThread = DtmThread(tid=newTask[0], returnInfo=(newTask[1],newTask[2],newTask[3]), target=newTask[6], args=newTask[7], kwargs=newTask[8], control=self)
                        newThread.start()

                        # On laisse au thread le temps de prendre le lock global d'execution
                        #time.sleep(0.001)
                        continue
                    except Queue.Empty:
                        pass

                    # Si on ne fait toujours rien
                    # on demande une nouvelle tache
                    self._askForTask()
                    
                time.sleep(DTM_CONTROL_THREAD_LATENCY)

            if self.commThread.isRootWorker:
                _printDtmMsg("DTM on rank " + str(self.workerId) + " receive an exit signal. Will quit NOW.")
            self._doCleanUp()


        def setOptions(self, *args, **kwargs):
            return
        
        def start(self, initialTarget):
            # On demarre le thread de communication

            self.commThread.start()

            self.commReadyEvent.wait()      # On attend que le thread de communication indique qu'il est pret
            
            # Sur le node principal (rank 0 dans le cas de MPI), on met la premiere tache dans la queue d'execution
            if self.commThread.isRootWorker:
                initTask = (self.idGenerator.tid, None, None, None, [self.workerId], time.time(), initialTarget, (), {})
                self.execQueue.put(initTask)

            self._main()


        # Les fonctions suivantes ne SONT PAS APPELEES PAR LE THREAD PRINCIPAL
        # Elles sont APPELEES PAR LES THREADS D'EXECUTION
        # TOUS LES OBJETS NON-LOCAUX QU'ELLES MODIFIENT _DOIVENT_ ETRE THREAD-SAFE
        # LES THREADS D'EXECUTION Y RESTENT BLOQUES TANT QUE LE RESULTAT N'ARRIVE PAS
        # (sauf pour les asynchrones, mais eux-memes vont creer un thread qui restera bloque)

        def map(self, function, iterable):
            listTid = []
            currentId = threading.currentThread().tid
            conditionObject = threading.currentThread().waitingCondition

            # On cree tout de suite l'espace pour recevoir les resultats
            self.resultsLock.acquire()
            self.results[currentId] = [None for i in xrange(0, len(iterable))]
            self.resultsLock.release()

            self.waitingThreadsLock.acquire()
            for index,elem in enumerate(iterable):
                task = (self.idGenerator.tid, self.workerId, currentId, (True, index), [self.workerId], time.time(), function, (elem,), {})
                listTid.append(task[0])
                self.execQueue.put(task)

            self.waitingThreads[currentId] = (conditionObject, listTid, time.time())
            self.waitingThreadsLock.release()

            time_wait = threading.currentThread().waitForCondition()        # On attend que les resultats soient disponibles

            # A ce point-ci, les resultats sont arrives ET on a le lock global d'execution (voir DtmThread.waitForCondition())
            self.resultsLock.acquire()
            ret = self.results[currentId]
            del self.results[currentId]
            self.resultsLock.release()

            # On revient au target du thread en retournant la liste des resultats
            return ret


        def map_async(self, function, iterable, callback = None):
            threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, target=function, args=iterable, control=self)
            asyncRequest = DtmAsyncResult(threadAsync, control=self)

            # On revient tout de suite au thread (pas de mise en pause)
            return asyncRequest

        def _apply(self, function, args, kwargs):
            currentId = threading.currentThread().tid
            conditionObject = threading.currentThread().waitingCondition

            # On cree tout de suite l'espace pour recevoir les resultats
            self.resultsLock.acquire()
            self.results[currentId] = [None]
            self.resultsLock.release()

            self.waitingThreadsLock.acquire()
            task = (self.idGenerator.tid, self.workerId, currentId, (True, 0), [self.workerId], time.time(), function, args, kwargs)
            listTid = [task[0]]
            self.execQueue.put(task)
            self.waitingThreads[currentId] = (conditionObject, listTid, time.time())
            self.waitingThreadsLock.release()

            time_wait = threading.currentThread().waitForCondition()        # On attend le resultat

            # A ce point-ci, le resultat est arrive ET on a le lock global d'execution (voir DtmThread.waitForCondition())
            self.resultsLock.acquire()
            ret = self.results[currentId]
            del self.results[currentId]
            self.resultsLock.release()

            # On revient au target du thread en retournant le resultat
            return ret[0]

        def apply(self, function, *args, **kwargs):
            return self._apply(function, args, kwargs)

        def apply_async(self, function, *args, **kwargs):
            threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, target=function, args=args, kwargs=kwargs, control=self, areArgsIterable = False)
            asyncRequest = DtmAsyncResult(threadAsync, control=self)
            return asyncRequest

        def imap(self, function, iterable, chunksize = 1):
            return None

        def imap_unordered(self, function, iterable, chunksize = 1):
            return None

        def filter(self, function, iterable):
            results = self.map(function, iterable)
            return [element for index,element in enumerate(iterable) if results[index]]

        def repeat(self, function, *args, **kwargs):
            return None

        def close(self):
            return None

        def terminate(self):
            return None


        def waitForAll(self):
            while True:
                self.asyncWaitingListLock.acquire()
                if len(self.asyncWaitingList.get(threading.currentThread().tid,[])) == 0:
                    self.asyncWaitingListLock.release()
                    break
                else:
                    self.waitingThreadsLock.acquire()
                    try:
                        waitingForCondition = self.waitingThreads[self.asyncWaitingList[threading.currentThread().tid][0]][0]
                    except KeyError:        # On vient tout juste de recevoir le dernier resultat (et l'entree dans le dictionnaire a ete supprimee)
                        self.waitingThreadsLock.release()
                        self.asyncWaitingListLock.release()
                        break

                    self.asyncWaitingListLock.release()
                    waitingForCondition.acquire()
                    self.waitingThreadsLock.release()
                    dtmGlobalExecutionLock.release()

                    waitingForCondition.wait()
                    waitingForCondition.release()
                    dtmGlobalExecutionLock.acquire()

            return None

        def testAllAsync(self):
            self.asyncWaitingListLock.acquire()
            retValue = (len(self.asyncWaitingList.get(threading.currentThread().tid,[])) == 0)
            self.asyncWaitingListLock.release()
            return retValue


        def getWorkerId(self):
            # With MPI, return the slot number
            return self.workerId


    # Methodes gerant le singleton
    # Inspire de http://all4dev.libre-entreprise.org/index.php/Le_singleton_en_python
    singletonInstance = None
    
    def __new__(c):
      if not DtmControl.singletonInstance:
          DtmControl.singletonInstance = DtmControl.__DtmControl()
      return DtmControl.singletonInstance

    def __getattr__(self, a):
      return getattr(self.singletonInstance, a)

    def __setattr__(self, a, value):
      return setattr(self.singletonInstance, a, value)

      
    

class DtmThread(threading.Thread):
    
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
        dtmGlobalExecutionLock.acquire()
        
        self.timeBegin = time.time()
        returnedR = self.t(*self.argsL, **self.kwargsL)
        self.timeExec += time.time() - self.timeBegin
        if self.isRootTask:
            # Si la tache racine est terminee alors on quitte
            self.control.exitStatus.set()
        else:
            resultTuple = (self.tid, self.returnInfo[1], self.returnInfo[2], self.timeExec, returnedR)
            self.control._returnResult(self.returnInfo[0], resultTuple)

        self.control.tasksStatsLock.acquire()
        self.control.tasksStats.setdefault(self.t,[]).append(self.timeExec)
        self.control.tasksStatsLock.release()
        
        dtmGlobalExecutionLock.release()


    def waitForCondition(self):
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

    def __init__(self, asyncThread, control):
        self.rThread = asyncThread
        self.dtmInterface = control
        self.resultReturned = False
        self.resultVal = None
        self.rThread.setObjToReturnTo(self)
        self.returnThread = threading.currentThread().tid
        
        self.dtmInterface.asyncWaitingListLock.acquire()
        self.dtmInterface.asyncWaitingList.setdefault(self.returnThread, []).append(self.rThread.tid)
        self.dtmInterface.asyncWaitingListLock.release()
        
        self.rThread.start()

    def _giveResult(self, result):
        # This method will be used by the async thread to return result
        self.resultReturned = True
        self.resultVal = result
        self.dtmInterface.asyncWaitingListLock.acquire()
        self.dtmInterface.asyncWaitingList.setdefault(self.returnThread, []).remove(self.rThread.tid)
        self.dtmInterface.asyncWaitingListLock.release()
    
    def get(self, timeout = None):
        if self.ready():
            return self.resultVal

        dtmGlobalExecutionLock.release()
        self.rThread.join(timeout)
        dtmGlobalExecutionLock.acquire()
        
        if self.rThread.isAlive():
            raise multiprocessing.TimeoutError("No result within the timeout for get()")
        return self.resultVal

    def wait(self, timeout = None):
        if self.ready():
            return

        dtmGlobalExecutionLock.release()
        self.rThread.join(timeout)
        dtmGlobalExecutionLock.acquire()
        
        if self.rThread.isAlive():
            raise multiprocessing.TimeoutError("join() returned before async thread had terminated")

    def ready(self):
        return not self.rThread.isAlive()

    def successful(self):
        if self.rThread.isAlive():
            raise AssertionError("Call DtmAsyncResult.successful() before the results were ready!")
        return True


dtm = DtmControl()