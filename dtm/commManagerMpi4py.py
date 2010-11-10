from mpi4py import MPI
import Queue
import time
import threading
import cPickle
#import pickle as cPickle
import numpy
#import array
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
        #buf = array.array('c', cPickle.dumps(msg))
        sBuf = cPickle.dumps(msg)
        arrayBuf = numpy.array(sBuf, dtype='a')
        
        #lMessageLenght = array.array('i', [self.currentId, len(buf), self.msgSendTag])
        lMessageLength = numpy.array([self.currentId, len(sBuf), self.msgSendTag], dtype='i')

        #if self.currentId == 0:
            #print(str(msg) + "###" + str(lMessageLength) + " ### " + str(len(buf)) + " ### " + str(self.msgSendTag) + "\n\n\n" + str(buf) + "\n\n\n")
        #else:
            #print("\t\t" + str(msg) + "###" + str(lMessageLength) + " ### " + str(len(buf)) + " ### " + str(self.msgSendTag))
        
        a=MPI.COMM_WORLD.Isend([lMessageLength, MPI.INT], dest=dest, tag=1)
        #a.Wait()
        b=MPI.COMM_WORLD.Isend([arrayBuf, MPI.BYTE], dest=dest, tag=self.msgSendTag)
        ##print("STOP SEND TEST")
        #while not b.Test() or not a.Test():
            #time.sleep(0.001)
        ##print("OK SEND FINISHED")
        self.msgSendTag += 1
        return a,b,lMessageLength,arrayBuf

    
    def run(self):
        lRecvWaiting = []
        lSendWaiting = []
        #lMessageNotif = array.array('L', [0,0,0])
        lMessageNotif = numpy.empty(3, dtype='i')   # Index 0 : Rank source, index 1 : taille du message, index 2 : tag du prochain message
        recvAsync = MPI.COMM_WORLD.Irecv([lMessageNotif, 3, MPI.INT], source=MPI.ANY_SOURCE, tag=1)
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
                #lBuf = array.array('c', ["#" for i in xrange(lMessageNotif[1])])
                lBuf = numpy.empty(lMessageNotif[1], dtype='a')
                
                lRecvWaiting.append((lBuf, MPI.COMM_WORLD.Irecv([lBuf, MPI.CHAR], source=lMessageNotif[0], tag=lMessageNotif[2])))
                
                #lMessageNotif = array.array('L', [0,0,0])
                lMessageNotif = numpy.empty(3, dtype='i')
                del recvAsync
                recvAsync = MPI.COMM_WORLD.Irecv([lMessageNotif, 3, MPI.INT], source=MPI.ANY_SOURCE, tag=1)
                recvSomething = True
                # La ligne suivante a demande 1 heure de recherche
                # Visiblement, de temps en temps, Wait() n'attend pas reellement jusqu'a la completion du receive.
                # Cela dit, ca plante encore de temps en temps avec dtm/tests/primes.py
	    
            for i,reqTuple in enumerate(lRecvWaiting):
                if reqTuple[1].Test():
                    strUnpickle = ""
                    #try:
                    self.recvQ.put(cPickle.loads(strUnpickle.join(reqTuple[0])))
                    #except cPickle.UnpicklingError:
                        #print("MPI TRANSFER ERROR. Received buffer follows.")
                        #print(reqTuple[0])
                        #raise cPickle.UnpicklingError
                    recvSomething = True
                    lRecvWaiting[i] = None
            lRecvWaiting = filter(lambda d: not d is None, lRecvWaiting)

            while True:
                # On envoie tous les messages
                try:
                    sendMsg = self.sendQ.get_nowait()
                    commA, commB, buf1, buf2 = self._mpiSend(sendMsg[1], sendMsg[0])
                    lSendWaiting.append((commA,buf1))
                    lSendWaiting.append((commB,buf2))
                    sendSomething = True
                except Queue.Empty:
                    break

            lSendWaiting = filter(lambda d: not d[0].Test(), lSendWaiting)
            
            if not recvSomething:
                time.sleep(DTM_MPI_LATENCY)