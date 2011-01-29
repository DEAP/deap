from mpi4py import MPI
import Queue
import time
import threading
import cPickle
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
        
        assert MPI.Is_initialized(), "Fatal error in MPI Init!"
        commReadyEvent.set()         # Send ready notification to the main thread
        
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
        # Buffer creation
        arrayBuf = array.array('c', cPickle.dumps(msg))
        
        # Create the MPI communication
        b=MPI.COMM_WORLD.Isend([arrayBuf, MPI.CHAR], dest=dest, tag=self.msgSendTag)

        self.msgSendTag += 1
        return b,arrayBuf

    
    def run(self):
        lRecvWaiting = []
        lSendWaiting = []
        countSend = 0
        countRecv = 0
        lMessageStatus = MPI.Status()
        working = True

        while working:
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():
                # Exiting
                # IMPORTANT : the communication thread MUST clear the sendQ
                # BEFORE exiting
                working = False

            while len(lRecvWaiting) < DTM_CONCURRENT_RECV_LIMIT and MPI.COMM_WORLD.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=lMessageStatus):
                # We receive something
                lBuf = array.array('c', '#'*lMessageStatus.Get_elements(MPI.CHAR))
                
                lRecvWaiting.append((lBuf, MPI.COMM_WORLD.Irecv([lBuf, MPI.CHAR], source=lMessageStatus.Get_source(), tag=lMessageStatus.Get_tag())))

                lMessageStatus = MPI.Status()
                recvSomething = True

            
            for i,reqTuple in enumerate(lRecvWaiting):
                # Check for completed receives
                if reqTuple[1].Test():
                    countRecv += 1
                    self.recvQ.put(cPickle.loads(reqTuple[0].tostring()))
                    lRecvWaiting[i] = None
                    recvSomething = True
            lRecvWaiting = [req for req in lRecvWaiting if req]

            while len(lSendWaiting) < DTM_CONCURRENT_SEND_LIMIT:
                # While we're not exceeding the concurrent communications max,
                # we clear the send queue
                try:
                    sendMsg = self.sendQ.get_nowait()
                except Queue.Empty:
                    break
                else:
                    countSend += 1
                    commA, buf1 = self._mpiSend(sendMsg[1], sendMsg[0])
                    lSendWaiting.append((commA,buf1))
                    sendSomething = True
            
            # Check for completed send (so the associated buffer may be freed)
            lSendWaiting = [req for req in lSendWaiting if not req[0].Test()]
            
            if not recvSomething:
                time.sleep(DTM_MPI_LATENCY)
                
        while len(lSendWaiting) > 0:
            # Sending the last queries
            lSendWaiting = [req for req in lSendWaiting if not req[0].Test()]
            time.sleep(DTM_MPI_LATENCY)
            
        del lSendWaiting
        del lRecvWaiting
        #del MPI
        