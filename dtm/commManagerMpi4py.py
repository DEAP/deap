from mpi4py import MPI
import Queue
import time
import threading
import cPickle
#import numpy
import array
import copy
import logging

import os

_logger = logging.getLogger("dtm.communication")

DTM_MPI_LATENCY = 0.01
DTM_CONCURRENT_RECV_LIMIT = 1000
DTM_CONCURRENT_SEND_LIMIT = 1000

class DtmCommThread(threading.Thread):

    def __init__(self, recvQ, sendQ, exitEvent, commReadyEvent):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        self.pSize = MPI.COMM_WORLD.Get_size()
        self.currentId = MPI.COMM_WORLD.Get_rank()
        self.exitStatus = exitEvent
        self.msgSendTag = 2
        
        assert MPI.Is_initialized(), "Error in MPI Init!"                
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
        arrayBuf = array.array('c', cPickle.dumps(msg))
        
        b=MPI.COMM_WORLD.Isend([arrayBuf, MPI.CHAR], dest=dest, tag=self.msgSendTag)

        self.msgSendTag += 1
        return b,arrayBuf

    
    def run(self):
        global MPI
        lRecvWaiting = []
        lSendWaiting = []
        countSend = 0
        countRecv = 0
        lMessageStatus = MPI.Status()
        working = True

        while working:
           # print(self.currentId, time.time())
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # On quitte
                # Note importante : le thread de communication DOIT vider la sendQ
                # AVANT de quitter (les ordres de quit doivent etre envoyes)
                working = False

            ##while recvAsync.Test():
            while len(lRecvWaiting) < DTM_CONCURRENT_RECV_LIMIT and MPI.COMM_WORLD.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=lMessageStatus):
                # On a recu quelque chose
                lBuf = array.array('c', ["#"]*lMessageStatus.Get_elements(MPI.CHAR))
                
                lRecvWaiting.append((lBuf, MPI.COMM_WORLD.Irecv([lBuf, MPI.CHAR], source=lMessageStatus.Get_source(), tag=lMessageStatus.Get_tag())))

                lMessageStatus = MPI.Status()
                recvSomething = True

            
            for i,reqTuple in enumerate(lRecvWaiting):
                if reqTuple[1].Test():
                    countRecv += 1
                    self.recvQ.put(cPickle.loads(reqTuple[0].tostring()))
                    lRecvWaiting[i] = None
                    recvSomething = True
            lRecvWaiting = [req for req in lRecvWaiting if req]
            #lRecvWaiting = filter(lambda d: not d is None, lRecvWaiting)

            while len(lSendWaiting) < DTM_CONCURRENT_SEND_LIMIT:
                # On envoie tous les messages
                try:
                    sendMsg = self.sendQ.get_nowait()
                    countSend += 1
                    commA, buf1 = self._mpiSend(sendMsg[1], sendMsg[0])
                    lSendWaiting.append((commA,buf1))
                    sendSomething = True
                except Queue.Empty:
                    break
            
            lSendWaiting = [req for req in lSendWaiting if req[0].Test()]
            #lSendWaiting = filter(lambda d: not d[0].Test(), lSendWaiting)
            
            if not recvSomething:
                time.sleep(DTM_MPI_LATENCY)
                
        while len(lSendWaiting) > 0:
            # On envoie les derniers messages
            lSendWaiting = [req for req in lSendWaiting if req[0].Test()]
            #lSendWaiting = filter(lambda d: not d[0].Test(), lSendWaiting)
            time.sleep(DTM_MPI_LATENCY)
            
        del lSendWaiting
        del lRecvWaiting
        #del MPI
        