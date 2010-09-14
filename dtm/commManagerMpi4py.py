from mpi4py import MPI
import Queue
import time
import threading
import cPickle
import numpy
import copy

DTM_MPI_LATENCY = 0.1

class DtmCommThread(threading.Thread):

    def __init__(self, recvQ, sendQ, exitEvent, commReadyEvent):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        self.pSize = MPI.COMM_WORLD.Get_size()
        self.currentId = MPI.COMM_WORLD.Get_rank()
        self.exitStatus = exitEvent
        self.msgSendTag = 2
        commReadyEvent.set()         # On doit notifier le thread principal qu'on est pret
        
    @property
    def poolSize(self):
        return self.pSize

    @property
    def workerId(self):
        return self.currentId

    @property
    def isRootWorker(self):
        return self.currentId == 0

    def iterOverIDs(self):
        return xrange(self.pSize)

    def _mpiSend(self, msg, dest):
        # Stupidite de mpi4py pourri qui demande des buffers en Python...
        # Pourquoi pas un GOTO tant qu'a y etre...
        buf = cPickle.dumps(msg)
        
        lMessageLenght = numpy.array([self.currentId, len(buf), self.msgSendTag], dtype='i')
        MPI.COMM_WORLD.Isend([copy.deepcopy(lMessageLenght), MPI.INT], dest=dest, tag=1)
        MPI.COMM_WORLD.Isend([copy.deepcopy(buf), MPI.CHAR], dest=dest, tag=self.msgSendTag)
        self.msgSendTag += 1

    
    def run(self):
        lMessageNotif = numpy.empty(3, dtype='i')   # Index 0 : Rank source, index 1 : taille du message, index 2 : tag du prochain message
        recvAsync = MPI.COMM_WORLD.Irecv([lMessageNotif, MPI.INT], source=MPI.ANY_SOURCE, tag=1)
        working = True

        while working:
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # On quitte
                # Note importante : le thread de communication DOIT vider la sendQ
                # AVANT de quitter (les ordres de quit doivent etre envoyes)
                working = False

            if recvAsync.Test():
                # On a recu quelque chose
                lBuf = numpy.empty(lMessageNotif[1], dtype='a')
                recvAsync2 = MPI.COMM_WORLD.Irecv([lBuf, MPI.CHAR], source=lMessageNotif[0], tag=lMessageNotif[2])
                strUnpickle = ""
                recvAsync2.Wait()
                assert recvAsync2.Test()
                
                # La ligne suivante a demande 1 heure de recherche
                # Visiblement, de temps en temps, Wait() n'attend pas reellement jusqu'a la completion du receive.
                # Cela dit, ca plante encore de temps en temps avec dtm/tests/primes.py
                time.sleep(0.02)
                try:
                    self.recvQ.put(cPickle.loads(strUnpickle.join(lBuf)))
                except cPickle.UnpicklingError:
                    print("MPI TRANSFER ERROR. Received buffer follows.")
                    print(lBuf)
                    raise cPickle.UnpicklingError
                
                lMessageNotif = numpy.empty(3, dtype='i')
                del recvAsync
                del recvAsync2
                recvAsync = MPI.COMM_WORLD.Irecv([lMessageNotif, MPI.INT], source=MPI.ANY_SOURCE, tag=1)
                recvSomething = True

            while True:
                # On envoie tous les messages
                try:
                    sendMsg = self.sendQ.get_nowait()
                    self._mpiSend(sendMsg[1], sendMsg[0])
                    sendSomething = True
                except Queue.Empty:
                    break

            if not recvSomething:
                time.sleep(DTM_MPI_LATENCY)