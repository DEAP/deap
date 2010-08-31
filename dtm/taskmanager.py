import threading
import time
import mpi
import random
import Queue
import sys

# Constantes
DTM_TAG_EXIT = 1
DTM_TAG_RETURN_TASK = 2
DTM_TAG_QUERY_TASK = 3
DTM_TAG_RETURN_RESULT = 4

DTM_MPI_LATENCY = 0.1
DTM_ASK_FOR_TASK_DELAY = 0.5


dtmGlobalExecutionLock = threading.Lock()


def _printDtmMsg(msg, gravity=1):
    print("#--------------- DTM ---------------#")
    print("# " + msg + "\n")


class DtmTaskIdGenerator(object):
    def __init__(self, rank = mpi.rank, initId = 0):
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
    Cette classe est le coeur de DTM. Elle est speciale au sens ou elle possede des methodes
    destinees aux threads d'execution, et d'autres destinees uniquement au thread principal
    start(), _main() et _doCleanUp() sont les methodes du thread principal (_main etant la boucle principale)
    Les autres methodes sont appelees (et executees dans) les threads d'EXECUTION
    """
    def __init__(self):
        self.sTime = time.time()
        self.curRank = mpi.rank
        self.poolSize = mpi.size
        
        self.waitingThreads = {}
        self.waitingThreadsLock = threading.Lock()

        self.asyncWaitingList = {}
        self.asyncWaitingListLock = threading.Lock()

        self.resultsLock = threading.Lock()
        self.results = {}

        self.tasksStatsLock = threading.Lock()
        self.tasksStats = {}
        
        self.idGenerator = DtmTaskIdGenerator()

        if self.curRank == 0:
            _printDtmMsg("DTM started with " + str(self.poolSize) + " workers")

        self.execQueue = Queue.Queue()
        
        self.sendResultsQueue = Queue.Queue()

        self.appStatusLock = threading.Lock()
        self.appStatus = [1,0,0,0]
        
        
        #self.updateReceiveThread.daemon = True
        self.mpiThread = DtmMpiCommThread(self.execQueue, self.sendResultsQueue, self.appStatus, self.appStatusLock, self.waitingThreads, self.waitingThreadsLock, self.results, self.resultsLock)
        #self.recvProcess.daemon = True


        
    def _doCleanUp(self):
        """
        Fonction charge de faire le clean up a la fin
        """
        if mpi.rank == 0:
            msgT = "Rank " + str(mpi.rank) + " ("+str(threading.currentThread().name)+" / " + str(threading.currentThread().ident) + ")\n"
            for target,times in self.tasksStats.items():
                try:
                    msgT += "\t" + str(target.__name__) + " : Avg=" + str(sum(times)/float(len(times))) + ", Min=" + str(min(times)) + ", Max=" + str(max(times)) + ", Total : " + str(sum(times)) + " used by " + str(len(times)) + " calls\n"
                except AttributeError:
                    msgT += "\t" + str(target) + " : Avg=" + str(sum(times)/float(len(times))) + ", Min=" + str(min(times)) + ", Max=" + str(max(times)) + ", Total : " + str(sum(times)) + " used by " + str(len(times)) + " calls\n"
            msgT += "\n"
            _printDtmMsg(msgT)

        self.mpiThread.join()

        del self.execQueue
        del self.sendResultsQueue

        countThreads = sum([1 for th in threading.enumerate() if not th.daemon])
        if countThreads > 1:
            print("Warning : there's more than 1 active thread at the exit (" + str(threading.activeCount()) + " total)\n" + str(threading.enumerate()))

        #mpi.finalize()

            
    
    def _main(self):
        """
        Dans cette fonction, get() et acquire() sont bloquants, on n'a pas besoin de sleep()
        """
        while self.appStatus[0] == 1:
            # Si on est deja en train d'executer un thread, ca ne sert a rien d'en ajouter un
            # Mieux vaut le laisser dans la execQueue, et peut-etre qu'un autre node libre
            # pourra le demander et l'executer avant nous
            #print(mpi.rank, "ENTREE DANS LA BOUCLE")
            dtmGlobalExecutionLock.acquire()    # On verifie deja si on est en train de faire quelque chose
            dtmGlobalExecutionLock.release()    # Tant que oui, on ne cree pas d'autre thread
                                                # On ne va pas non plus rechercher si on a des resultats
                                                # De toute facon, le thread en attente devrait attendre le global lock pour reprendre

            newTask = self.execQueue.get()
            if newTask is None or self.appStatus[0] != 1:
                break
            #try:
                #newTask = self.execQueue.get(True, 0.1)      # Ok, on est libre, on demande une tache
            #except (Queue.Empty,IOError):
                #continue

            # On verifie que on ne fait toujours rien
            # (le delai du get() peut etre long et une tache en wait peut etre revenue)
            # Si on s'est mis a faire quelque chose, on remet la tache dans la queue
            # Bon on la remet a la fin et c'est pas optimal, mais c'est un debut...
            if not dtmGlobalExecutionLock.acquire(False):
                self.execQueue.put(newTask)
                continue
            else:
                dtmGlobalExecutionLock.release()

            #print("CREATION DU THREAD")
            # Ici il est trop tard pour reculer, on cree le thread et on l'initialise
            # Si un autre thread a repris le lock, ce thread ci devra attendre
            newThread = DtmThread(tid=newTask[0], returnInfo=(newTask[1],newTask[2],newTask[3]), target=newTask[6], args=newTask[7], kwargs=newTask[8], control=self)
            newThread.start()
            #time.sleep(0.01)     # On laisse le temps au thread de reprendre le verrou

        if self.curRank == 0:
            _printDtmMsg("DTM on rank " + str(self.curRank) + " receive an exit signal. Will quit NOW.")
        self._doCleanUp()

    
    def start(self, initialTarget):       
        # On demarre les processus de communication
        
        self.mpiThread.start()
        
        # Sur le rank 0, on met la premiere tache dans la queue d'execution
        if self.curRank == 0:
            initTask = (self.idGenerator.tid, None, None, None, [self.curRank], time.time(), initialTarget, (), {})
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
            task = (self.idGenerator.tid, mpi.rank, currentId, (True, index), [mpi.rank], time.time(), function, (elem,), {})
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

    
    def map_async(self, function, iterable, callback = None, chunksize = 1):
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
        task = (self.idGenerator.tid, mpi.rank, currentId, (True, 0), [mpi.rank], time.time(), function, args, kwargs)
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
                #print(type(waitingFor), type(waitingFor[0]))
                waitingForCondition.acquire()
                self.waitingThreadsLock.release()
                self.appStatus[3] = 0
                dtmGlobalExecutionLock.release()

                waitingForCondition.wait()
                waitingForCondition.release()
                dtmGlobalExecutionLock.acquire()
                self.appStatus[3] = 1
                
        return None

    def testAllAsync(self):
        self.asyncWaitingListLock.acquire()
        retValue = (len(self.asyncWaitingList.get(threading.currentThread().tid,[])) == 0)
        self.asyncWaitingListLock.release()
        return retValue


    def getWorkerId(self):
        # With MPI, return the slot number
        return self.curRank

    

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
        self.control.appStatus[3] = 1
        
        self.timeBegin = time.time()
        returnedR = self.t(*self.argsL, **self.kwargsL)
        self.timeExec += time.time() - self.timeBegin
        
        if self.isRootTask:
            # Si la tache racine est terminee alors on quitte
            self.control.appStatus[0] = 0
            self.control.execQueue.put(None)
        else:
            self.control.sendResultsQueue.put([self.returnInfo[0], self.tid, self.returnInfo[1], self.returnInfo[2], 0, returnedR])
        #if mpi.rank != 0:
            #print(mpi.rank, "Thread will end up (or it should...)", returnedR)
        self.control.appStatus[3] = 0
        dtmGlobalExecutionLock.release()

        self.control.tasksStatsLock.acquire()
        self.control.tasksStats.setdefault(self.t,[]).append(self.timeExec)
        self.control.tasksStatsLock.release()
        

    def waitForCondition(self):
        self.waitingCondition.acquire()
        self.control.appStatus[3] = 0
        beginTimeWait = time.time()
        self.timeExec += beginTimeWait - self.timeBegin
        dtmGlobalExecutionLock.release()
        
        self.waitingCondition.wait()
        self.waitingCondition.release()
        
        dtmGlobalExecutionLock.acquire()
        self.timeBegin = time.time()
        self.control.appStatus[3] = 1
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

        threading.currentThread().control.appStatus[3] = 0
        dtmGlobalExecutionLock.release()
        self.rThread.join(timeout)
        dtmGlobalExecutionLock.acquire()
        threading.currentThread().control.appStatus[3] = 1
        
        if self.rThread.isAlive():
            raise multiprocessing.TimeoutError("No result within the timeout for get()")
        return self.resultVal

    def wait(self, timeout = None):
        if self.ready():
            return

        threading.currentThread().control.appStatus[3] = 0
        dtmGlobalExecutionLock.release()
        self.rThread.join(timeout)
        dtmGlobalExecutionLock.acquire()
        threading.currentThread().control.appStatus[3] = 1
        
        if self.rThread.isAlive():
            raise multiprocessing.TimeoutError("join() returned before async thread had terminated")

    def ready(self):
        return not self.rThread.isAlive()

    def successful(self):
        if self.rThread.isAlive():
            raise AssertionError("Call DtmAsyncResult.successful() before the results were ready!")
        return True



class DtmMpiCommThread(threading.Thread):

    def __init__(self, execQ, sendQ, appStatus, appStatusLock, waitingT, waitingTLock, resultsDict, resultsDictLock):
        threading.Thread.__init__(self)
        self.execQ = execQ
        self.sendQ = sendQ
        self.nodesStatus = [[1,0,time.time(), time.time()] if i == 0 else [0,0,time.time(), time.time()] for i in xrange(mpi.size)]
        self.appStatus = appStatus
        self.appStatusLock = appStatusLock
        self.waitingT = waitingT
        self.resultsDict = resultsDict
        self.waitingTLock = waitingTLock
        self.resultsDictLock = resultsDictLock
        self.rankMpi = mpi.rank

    def _updateNodesDict(self, fromNodeNumber, newDict):
        #print("BEFORE UPDATE", self.nodesStatus[:])
        #print("RECEIVE DICT ", newDict)
        rankMpi = self.rankMpi
        for i in xrange(len(newDict)):
            if (i == fromNodeNumber or newDict[i][2] > self.nodesStatus[i][2]) and i != rankMpi:
                self.nodesStatus[i] = newDict[i]

        #print("AFTER UPDATE", self.nodesStatus[:])

    def _dispatchResult(self, result):
        tidParent = result[1]

        self.resultsDictLock.acquire()
        if result[2][0]:    # Le resultat est un iterable
            self.resultsDict[tidParent][result[2][1]] = result[4]
        else:
            self.resultsDict[tidParent] = result[4]
        self.resultsDictLock.release()

        self.waitingTLock.acquire()
        self.waitingT[tidParent][1].remove(result[0])
        if len(self.waitingT[tidParent][1]) == 0:      # Tous les resultats sont arrives
            conditionLock = self.waitingT[tidParent][0]
            del self.waitingT[tidParent]              # On supprime la tache d'attente
            conditionLock.acquire()     # On avertit le thread qu'il peut reprendre
            conditionLock.notifyAll()
            conditionLock.release()

        self.waitingTLock.release()

    
    def run(self):
        rankMpi = self.rankMpi
        #print("Im the send/receive process ", multiprocessing.current_process().pid)
        #print("\tOn rank " + str(rankMpi))
        recvExit = mpi.irecv(tag=DTM_TAG_EXIT)
        recvResult = mpi.irecv(tag=DTM_TAG_RETURN_RESULT)
        recvTask = mpi.irecv(tag=DTM_TAG_RETURN_TASK)
        recvAskForTasks = mpi.irecv(tag=DTM_TAG_QUERY_TASK)
        

        while True:
            receiveSomething = False
            self.appStatusLock.acquire()
            if self.appStatus[3] == 0:
                self.appStatus[1] = 0
            else:
                self.appStatus[1] = self.execQ.qsize()        # ATTENTION A MAC OS X (NotImplementedError) -- a verifier


            self.waitingTLock.acquire()
            if len(self.waitingT) == 0:
                self.waitingTLock.release()
                self.appStatus[2] = 0
            else:
                self.appStatus[2] = len(self.waitingT)
                self.waitingTLock.release()

            
            if self.appStatus[0] != 1:
                self.appStatusLock.release()
                if rankMpi == 0:
                    # Si on quitte, on doit l'annoncer a tout le monde
                    # C'est le rank 0 qui va propager le message
                    #print("******* ON QUITTE")
                    for i in xrange(mpi.size):
                        if i == rankMpi:
                            continue
                        #print("******* ENVOI DU MESSAGE DE QUIT A " + str(i))
                        mpi.isend([0, self.appStatus[0], "Terminus!"], i, tag=DTM_TAG_EXIT)
                        #print("************ FIN DE L'ENVOI")
                del recvResult
                del recvExit
                del recvTask
                del recvAskForTasks
                break
                
            if recvExit:
                # On quitte
                #print(mpi.rank, "RECEIVE EXIT")
                exitInfo = recvExit.message
                self.appStatus[0] = exitInfo[1]

                #Hack temporaire
                self.execQ.put(None)
                self.appStatusLock.release()
                break
                
            self.appStatusLock.release()

            if recvResult:
                receiveSomething = True
                resultData = recvResult.message
                self._updateNodesDict(resultData[0], resultData[1])
                self._dispatchResult(resultData[2])
                recvResult = mpi.irecv(tag=DTM_TAG_RETURN_RESULT)

            if recvAskForTasks:
                receiveSomething = True
                rankInfo = recvAskForTasks.message
                self._updateNodesDict(rankInfo[0], rankInfo[1])
                #time.sleep(0.1)
                recvAskForTasks = mpi.irecv(tag=DTM_TAG_QUERY_TASK)

            if recvTask:
                receiveSomething = True
                taskDataList = recvTask.message
                for taskData in taskDataList[3]:
                    self.execQ.put(taskData)
                self._updateNodesDict(taskDataList[0], taskDataList[1])
                #time.sleep(0.1)
                recvTask = mpi.irecv(tag=DTM_TAG_RETURN_TASK)


            # On met a jour NOTRE load
            # Avant de commencer d'eventuelles operations d'envoi
            self.appStatusLock.acquire()
            self.nodesStatus[rankMpi] = [self.appStatus[1], self.appStatus[2], time.time(), time.time()]
            currentExecStatus = self.appStatus[3]
            self.appStatusLock.release()

            didSomething = False
            if not self.sendQ.empty():
                # On a des donnees a envoyer
                while True:
                    try:
                        data = self.sendQ.get_nowait()
                        if data[0] == rankMpi:     # On ne s'envoie pas de message a nous-memes
                            self._dispatchResult(data[1:])
                            continue
                        mpi.isend([rankMpi, self.nodesStatus[:], data[1:]], data[0], tag=DTM_TAG_RETURN_RESULT)
                        didSomething = True
                    except Queue.Empty:
                        break
            
            if not currentExecStatus:
                # Si on a rien a faire, on envoie notre status aux autres

                # On choisit un node au hasard
                # Toutefois, on s'assure qu'on ne l'a pas contacte depuis un certain delai
                # (pour eviter de l'occuper a juste repondre a des demandes de taches)
                curTime = time.time()
                nodeWorking = [i for i,n in enumerate(self.nodesStatus) if n[0] > 0 and i != rankMpi and curTime - n[3] > DTM_ASK_FOR_TASK_DELAY]
                if len(nodeWorking) > 0:
                    chosenNode = random.choice(nodeWorking)
                    mpi.isend([rankMpi, self.nodesStatus[:], time.time()], chosenNode, tag=DTM_TAG_QUERY_TASK)
                    #didSomething = True
                # Il est possible qu'on n'envoie rien si tous les nodes occupes ont ete contactes depuis moins de DTM_ASK_FOR_TASK_DELAY

            else:
                # On cherche si on pourrait envoyer la tache quelque part
                currentSelfLoad = self.nodesStatus[rankMpi]
                availableNodes = [i for i,n in enumerate(self.nodesStatus) if n[0] < currentSelfLoad[0] and i != rankMpi]
                #print("BOUM", rankMpi, availableNodes)
                if len(availableNodes) > 0:
                    # Cool il y a un slot de libre
                    chosenSlot = random.choice(availableNodes)
                    
                    # On essaie de dispatcher equitablement les taches
                    nbrTask = self.execQ.qsize() / mpi.size
                    if nbrTask == 0:
                        nbrTask = 1
                        
                    try:
                        taskList = []
                        try:
                            for t in xrange(nbrTask):
                                taskList.append(self.execQ.get_nowait())
                        except Queue.Empty:
                            if len(taskList) == 0:
                                raise Queue.Empty       # Si on a aucune tache a envoyer, on va au prochain catch
                            else:
                                pass                    # Sinon, on envoie ce qu'on peut
                            
                        # On lui envoie la tache
                        nbrTask = len(taskList)
                        mpi.isend([rankMpi, self.nodesStatus[:], nbrTask, taskList], chosenSlot, tag=DTM_TAG_RETURN_TASK)

                        #On peut supposer que le noeud aura maintenant 'nbrTask' taches de plus dans son execQ
                        self.nodesStatus[chosenSlot][0] += nbrTask
                        didSomething = True
                    except Queue.Empty: # On a rien a lui donner
                        pass
            
            if not receiveSomething and not didSomething:
                # Si on a recu quelque8 chose, on veut retester tout de suite
                # donc pas de pause dans ce cas la
                time.sleep(DTM_MPI_LATENCY)
        #print("FIN DU PROCESS DE COMMUNICATION")
        time.sleep(0.1)

