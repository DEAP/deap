import threading
import time
import random
import Queue
from commManager import DtmCommThread

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
    Genere les IDs des taches (thread-safe)
    Un ID est un tuple de la forme (workerId, numero unique)
    Avec MPI, workerId est un entier (le rank), et les numeros uniques commencent a 0
    Mais rien n'empeche que le workerId soit autre chose, sous la restriction qu'il soit immutable
    (car il doit pouvoir servir de cle de dictionnaire)
    """
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
    """
    Classe encapsulant le "vrai" DtmControl, afin de s'assurer que l'utilisateur
    ne cree qu'une seule instance du taskmanager
    """

    class __DtmControl:
        """
        Cette classe est le coeur de DTM.
        Elle est speciale au sens ou elle possede des methodes destinees aux threads d'execution,
        et d'autres destinees uniquement au thread principal (thread de controle)

        Les methodes start() et setOptions() sont appelees par l'utilisateur DANS LE THREAD PRINCIPAL.

        Les methodes map(), apply(), map_async(), filter(), terminate(), etc...
        sont appelees par l'utilisateur DANS LES THREADS D'EXECUTION

        Les methodes cachees (prefixees de _) sont reservees a l'usage interne de DTM.
        L'utilisateur ne devrait jamais avoir a les appeler.
        Toutes ces methodes cachees, sauf _apply() et _returnResult,
        sont appelees uniquement par le thread de controle

        Cette classe n'est pas dependante du backend de communication utilise, en autant que ce backend
        fournisse une API definie
        """
        def __init__(self):
            self.sTime = time.time()

            # Contient les threads qui sont en attente synchrone de resultats
            # La cle du dictionnaire est le task Id de la tache en attente
            self.waitingThreads = {}
            self.waitingThreadsLock = threading.Lock()

            # Contient la liste des taches asynchrones lancees par un thread
            # La cle du dictionnaire est le task Id de la tache qui a lance les taches asynchrones
            self.asyncWaitingList = {}
            self.asyncWaitingListLock = threading.Lock()

            # Contient les resultats d'une tache (lieu de stockage temporaire en attendant que tout soit recu)
            # La cle du dictionnaire est le task Id de la tache a qui vont aller ces resultats
            self.resultsLock = threading.Lock()
            self.results = {}

            # Contient les statistiques sur les taches (la cle du dictionnaire est le __name__ d'une fonction)
            self.tasksStatsLock = threading.Lock()
            self.tasksStats = {}


            # Queues d'execution
            # waitingForRestartQueue contient les locks conditionnels des threads qui etaient en attente
            # de resultats qui ont tous ete recus. Cette queue est prioritaire sur
            # execQueue, qui contient des taches non encore demarrees (qui peuvent donc migrer)
            self.waitingForRestartQueue = Queue.Queue()
            self.execQueue = Queue.Queue()

            # Queues partages (communication)
            self.recvQueue = Queue.Queue()
            self.sendQueue = Queue.Queue()

            # Declenche par la tache root lorsque termine
            self.exitStatus = threading.Event()

            # Permet d'indiquer au thread de communication la fin du programme
            self.commExitNotification = threading.Event()

            # Permet au thread de communication d'indiquer qu'il est pret
            self.commReadyEvent = threading.Event()

            self.exitState = (None, None)

            # Thread de communication; lance dans DtmControl.start()
            self.commThread = DtmCommThread(self.recvQueue, self.sendQueue, self.commExitNotification, self.commReadyEvent)

            self.poolSize = self.commThread.poolSize
            self.workerId = self.commThread.workerId

            # On initialise le generateur de task Id
            self.idGenerator = DtmTaskIdGenerator(self.workerId)

            # Cette liste contient les loads des differents workers
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
                msgT += "\t" + str(target) + " : Avg=" + str(sum(times)/float(len(times))) + ", Min=" + str(min(times)) + ", Max=" + str(max(times)) + ", Total : " + str(sum(times)) + " used by " + str(len(times)) + " calls\n"
            msgT += "\n"
            _printDtmMsg(msgT)

            if self.commThread.isRootWorker:
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
            self.results[tidParent][result[2]] = result[4]
            self.resultsLock.release()

            self.waitingThreadsLock.acquire()

            self.waitingThreads[tidParent][1].remove(result[0])
            if len(self.waitingThreads[tidParent][1]) == 0:      # Tous les resultats sont arrives
                conditionLock = self.waitingThreads[tidParent][0]
                del self.waitingThreads[tidParent]              # On supprime la tache d'attente
                
                for listAsync in self.asyncWaitingList.values():
                    if tidParent in listAsync:
                        # Les threads asynchrones sont relances tout de suite puisqu'ils n'ont pas besoin du lock d'execution
                        conditionLock.acquire()
                        conditionLock.notifyAll()
                        conditionLock.release()
                        self.waitingThreadsLock.release()
                        return

                # Les threads synchrones sont mis en attente d'execution
                self.waitingForRestartQueue.put(conditionLock)

            self.waitingThreadsLock.release()

        def _main(self):
            # Cette fonction est la boucle principale du thread de controle
            
            while True:
                # On update notre etat
                self.nodesStatus[self.workerId] = [self.execQueue.qsize(), self.waitingForRestartQueue.qsize(), len(self.waitingThreads), time.time(), time.time()]

                # On verifie les messages recus
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
                    except Queue.Empty:     # On a plus rien a recevoir
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

                        # On peut supposer que le noeud aura maintenant 'nbrTask' taches de plus dans son execQ
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
                        continue
                    except Queue.Empty:
                        pass

                    try:
                        # On recupere une nouvelle tache dans la queue d'execution
                        newTask = self.execQueue.get_nowait()
                        newThread = DtmThread(tid=newTask[0], returnInfo=(newTask[1],newTask[2],newTask[3]), target=newTask[6], args=newTask[7], kwargs=newTask[8], control=self)
                        newThread.start()

                        continue
                    except Queue.Empty:
                        pass

                    # Si on ne fait toujours rien
                    # on demande une nouvelle tache
                    self._askForTask()

                # Si on n'a rien a faire ou que on est deja en train d'executer quelque chose
                # On attend un peu
                time.sleep(DTM_CONTROL_THREAD_LATENCY)

            if self.commThread.isRootWorker:
                _printDtmMsg("DTM on rank " + str(self.workerId) + " receive an exit signal. Will quit NOW.")
            self._doCleanUp()


        def setOptions(self, *args, **kwargs):
            # Pas encore implementee
            # Sera utilisee pour modifier des options du taskmanager (latence, etc.)
            # Sauf si on veut vraiment s'attirer du trouble, l'ideal serait de ne l'appeller
            # QUE dans le thread principal (i.e. avant que start() ne soit execute)
            return
        
        def start(self, initialTarget):
            # On demarre le thread de communication

            self.commThread.start()

            self.commReadyEvent.wait()      # On attend que le thread de communication indique qu'il est pret
            
            # Sur le node principal (rank 0 dans le cas de MPI), on met la premiere tache dans la queue d'execution
            if self.commThread.isRootWorker:
                initTask = (self.idGenerator.tid, None, None, None, [self.workerId], time.time(), initialTarget, (), {})
                self.execQueue.put(initTask)

            # Entree dans la boucle principale
            self._main()


        # Les fonctions suivantes ne SONT PAS APPELEES PAR LE THREAD PRINCIPAL
        # Elles sont APPELEES PAR LES THREADS D'EXECUTION
        # TOUS LES OBJETS NON-LOCAUX QU'ELLES MODIFIENT _DOIVENT_ ETRE THREAD-SAFE
        # LES THREADS D'EXECUTION Y RESTENT BLOQUES TANT QUE LE RESULTAT N'ARRIVE PAS
        # (sauf pour les asynchrones, mais eux-memes vont creer un thread qui restera bloque)

        def map(self, function, iterable):
            # Pour l'instant, map() ne supporte pas plusieurs iterables
            # En concordance avec l'API de multiprocessing
            # A discuter...
            
            listTid = []
            currentId = threading.currentThread().tid
            conditionObject = threading.currentThread().waitingCondition

            # On cree tout de suite l'espace pour recevoir les resultats
            self.resultsLock.acquire()
            self.results[currentId] = [None for i in xrange(0, len(iterable))]
            self.resultsLock.release()

            # On cree toutes les taches et on les ajoute a la queue d'execution
            self.waitingThreadsLock.acquire()
            for index,elem in enumerate(iterable):
                task = (self.idGenerator.tid, self.workerId, currentId, index, [self.workerId], time.time(), function, (elem,), {})
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
            # Callback n'est pas encore implemente

            # On cree un thread special, qui "attendra pour nous"
            # ainsi qu'une structure fournissant l'API de multiprocessing.AsyncResult
            threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, target=function, args=iterable, control=self)
            asyncRequest = DtmAsyncResult(threadAsync, control=self)

            # On revient tout de suite au thread (pas de mise en pause)
            return asyncRequest
            

        def _apply(self, function, args, kwargs):
            # Fonction qui permet de regrouper apply() et apply_async()
            currentId = threading.currentThread().tid
            conditionObject = threading.currentThread().waitingCondition

            # On cree tout de suite l'espace pour recevoir les resultats
            self.resultsLock.acquire()
            self.results[currentId] = [None]
            self.resultsLock.release()

            # On cree la tache et on la met sur la queue d'execution
            self.waitingThreadsLock.acquire()
            task = (self.idGenerator.tid, self.workerId, currentId, 0, [self.workerId], time.time(), function, args, kwargs)
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
            # Voir map_async
            threadAsync = DtmAsyncWaitingThread(tid=self.idGenerator.tid, target=function, args=args, kwargs=kwargs, control=self, areArgsIterable = False)
            asyncRequest = DtmAsyncResult(threadAsync, control=self)
            return asyncRequest

        def imap(self, function, iterable, chunksize = 1):
            # Not implemented
            raise NotImplementedError

        def imap_unordered(self, function, iterable, chunksize = 1):
            # Not implemented (vraiment utile par rapport a imap?)
            raise NotImplementedError

        def filter(self, function, iterable):
            # Le filtrage s'effectue dans ce thread, mais le calcul est distribue
            results = self.map(function, iterable)
            return [element for index,element in enumerate(iterable) if results[index]]

        def repeat(self, function, howManyTimes, *args, **kwargs):
            # Repete une fonction avec les memes arguments et renvoie une liste contenant les resultats
            # Pas encore implemente
            results = [None for i in xrange(howManyTimes)]
            return results

        def terminate(self):
            # Termine l'execution
            # Comportement plus ou moins defini avec MPI si appele sur autre chose que le rank 0
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


    # Methodes gerant le singleton
    # Inspire de http://all4dev.libre-entreprise.org/index.php/Le_singleton_en_python
    singletonInstance = None
    
    def __new__(c):
        if not DtmControl.singletonInstance:
            DtmControl.singletonInstance = DtmControl.__DtmControl()
        return DtmControl.singletonInstance

    def __getattr__(self, a):
        # Renvoie aux methodes correspondantes de __DtmControl
        return getattr(self.singletonInstance, a)

    def __setattr__(self, a, value):
        return setattr(self.singletonInstance, a, value)

      
    

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
    La classe correspondante a multiprocessing.AsyncResult
    Elle offre sensiblement la meme interface, a l'exception notable pret des timeout
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
        if self.ready():
            return self.resultVal
        self.wait()
        
        return self.resultVal

    def wait(self):
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
        return not self.rThread.isAlive()

    def successful(self):
        if self.rThread.isAlive():
            raise AssertionError("Call DtmAsyncResult.successful() before the results were ready!")
        return self.resultReturned

# On cree une instance du taskmanager (qui pourra etre importee directement)
dtm = DtmControl()