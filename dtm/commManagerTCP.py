from multiprocessing.connection import Client,Listener
import Queue
import time
import threading
import sys

DTM_COMM_LATENCY = 0.1

# Les communications par multiprocessing.connection ont le defaut
# de demander enormement de connexions (1 entre chaque paire de workers)
# soit au total n*(n-1)/2 connexions ouvertes pour n workers
# Les ports sont automatiquement attribues a partir du numero ci-dessous
BASE_COMM_PORTS = 50000

class DtmCommThread(threading.Thread):

    def __init__(self, recvQ, sendQ, exitEvent, commReadyEvent):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        self.exitStatus = exitEvent

        # On tente de retrouver les infos de demarrage sur la ligne de commande
        self.workersFile = None
        self.wId = None
        nextElem = None
        for elem in sys.argv[1:]:
            if elem == '-f':
                nextElem = "workersFile"
            elif elem == '-i':
                nextElem = "workerId"
            elif nextElem == "workersFile":
                self.workersFile = elem
            elif nextElem == "workerId":
                self.wId = int(elem)
            else:
                nextElem = None

        assert not self.workersFile is None
        assert not self.wId is None

        
        # On ouvre le fichier des workers
        fWorkers = open(self.workersFile, 'r')
        listWorkers = fWorkers.readlines()
        self.pSize = len(listWorkers)

        self.address = listWorkers[self.wId]

        self.connections = []
        self.listeners = []
        for wid,remoteAddr in enumerate(listWorkers):
            if wid == self.wId:
                self.connections.append(None)
                continue
            # Si notre ID est SUPERIEUR a celui du remote process, c'est NOUS qui creons le client
            # Sinon, on cree un objet Listener qui tente de se connecter au client
            if self.wId > wid:
                self.connections.append(Client((self.address, BASE_COMM_PORTS + self.wId*self.pSize + wid)))    # Attention, call bloquant
                #print("End creation")
            else:
                tmpListener = Listener((remoteAddr, BASE_COMM_PORTS + wid*self.pSize + self.wId))
                self.listeners.append(tmpListener)
                self.connections.append(tmpListener.accept())       # Attention, call bloquant

        commReadyEvent.set()         # On doit notifier le thread principal qu'on est pret
        
    @property
    def poolSize(self):
        return self.pSize

    @property
    def workerId(self):
        return self.wId

    @property
    def isRootWorker(self):
        return self.wId == 0

    def iterOverIDs(self):
        return xrange(self.pSize)

    def run(self):
        working = True

        while working:
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # On quitte
                # Note importante : le thread de communication DOIT vider la sendQ
                # AVANT de quitter (les ordres de quit doivent etre envoyes)
                working = False

            # On poll les connexions
            for conn in self.connections:
                if conn is None:    # On ne recoit pas de messages de nous-memes
                    continue
                if conn.poll():
                    # On a recu quelque chose
                    try:
                        self.recvQ.put(conn.recv())
                    except EOFError:
                        working = False
                    recvSomething = True

            while True:
                # On envoie tous les messages
                try:
                    sendMsg = self.sendQ.get_nowait()
                    self.connections[sendMsg[0]].send(sendMsg[1])
                    sendSomething = True
                except Queue.Empty:
                    break

            if not recvSomething:
                time.sleep(DTM_COMM_LATENCY)

        for listener in self.listeners:
            listener.close()