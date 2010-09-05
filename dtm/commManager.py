import mpi
import Queue
import time
import threading

DTM_MPI_LATENCY = 0.1

class DtmCommThread(threading.Thread):

    def __init__(self, recvQ, sendQ, exitEvent, commReadyEvent):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        self.pSize = mpi.size
        self.currentId = mpi.rank
        self.exitStatus = exitEvent
        commReadyEvent.set()         # On doit notifier le thread principal qu'on est prets
        
    @property
    def poolSize(self):
        return self.pSize

    @property
    def workerId(self):
        return self.currentId

    @property
    def isRootWorker(self):
        return self.currentId == 0

    def run(self):
        recvAsync = mpi.irecv()
        working = True

        while working:
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # On quitte
                working = False

            if recvAsync:
                # On a recu quelque chose
                self.recvQ.put(recvAsync.message)
                recvAsync = mpi.irecv()
                recvSomething = True

            while True:
                # On envoie tous les messages
                try:
                    sendMsg = self.sendQ.get_nowait()
                    mpi.isend(sendMsg[1], sendMsg[0])
                    sendSomething = True
                except Queue.Empty:
                    break

            if not recvSomething:
                time.sleep(DTM_MPI_LATENCY)