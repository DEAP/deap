from mpi4py import MPI
try:
    import Queue
except ImportError:
    import queue as Queue
import time
import threading
try:
    import cPickle
except ImportError:
    import pickle as cPickle
import array
import copy
import logging

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        # Python 2.5
        import xml.etree.ElementTree as etree

import os

from deap.dtm.dtmTypes import *

_logger = logging.getLogger("dtm.communication")

DTM_MPI_MIN_LATENCY = 0.005
DTM_MPI_MAX_LATENCY = 0.01
DTM_CONCURRENT_RECV_LIMIT = 1000
DTM_CONCURRENT_SEND_LIMIT = 1000

class DtmCommThread(threading.Thread):

    def __init__(self, recvQ, sendQ, mainThreadEvent, exitEvent, commReadyEvent, randomGenerator):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        self.pSize = MPI.COMM_WORLD.Get_size()
        self.currentId = MPI.COMM_WORLD.Get_rank()
        self.exitStatus = exitEvent
        self.msgSendTag = 2
        self.wakeUpMainThread = mainThreadEvent
        self.random = randomGenerator
        
        self.traceMode = False
        self.traceTo = None
        
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
    
    def setTraceModeOn(self, xmlLogger):
        self.traceMode = True
        self.traceTo = xmlLogger

    def iterOverIDs(self):
        return range(self.pSize)

    def _mpiSend(self, msg, dest):
        # Stupidite de mpi4py pourri qui demande des buffers en Python...
        # Pourquoi pas un GOTO tant qu'a y etre...
        arrayBuf = array.array('b')
        arrayBuf.fromstring(cPickle.dumps(msg))
        #arrayBuf = array.array('c', cPickle.dumps(msg))
        
        b = MPI.COMM_WORLD.Isend([arrayBuf, MPI.CHAR], dest=dest, tag=self.msgSendTag)
        if self.traceMode:
            etree.SubElement(self.traceTo, "msg", {"direc" : "out", "type" : str(msg.msgType), "otherWorker" : str(dest), "msgtag" : str(self.msgSendTag), "time" : str(time.time())})
        
        self.msgSendTag += 1
        return b, arrayBuf

    
    def run(self):
        global MPI
        lRecvWaiting = []
        lSendWaiting = []
        countSend = 0
        countRecv = 0
        lMessageStatus = MPI.Status()
        working = True
        
        countRecvNotTransmit = 0
        countRecvTimeInit = time.time()

        while working:
           # print(self.currentId, time.time())
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # On quitte
                # Note importante : le thread de communication DOIT vider la sendQ
                # AVANT de quitter (les ordres de quit doivent etre envoyes)
                working = False

            while len(lRecvWaiting) < DTM_CONCURRENT_RECV_LIMIT and MPI.COMM_WORLD.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=lMessageStatus):
                # On a recu quelque chose
                lBuf = array.array('b')
                lBuf.fromlist([0] * lMessageStatus.Get_elements(MPI.CHAR))
                #lBuf = array.array('c', ["#"]*lMessageStatus.Get_elements(MPI.CHAR))
                
                lRecvWaiting.append((lBuf, MPI.COMM_WORLD.Irecv([lBuf, MPI.CHAR], source=lMessageStatus.Get_source(), tag=lMessageStatus.Get_tag()), lMessageStatus.Get_tag()))

                lMessageStatus = MPI.Status()
                recvSomething = True

            
            for i, reqTuple in enumerate(lRecvWaiting):
                if reqTuple[1].Test():
                    countRecv += 1
                    dataS = cPickle.loads(reqTuple[0].tostring())
                    if self.traceMode:
                        etree.SubElement(self.traceTo, "msg", {"direc" : "in", "type" : str(dataS.msgType), "otherWorker" : str(dataS.senderWid), "msgtag" : str(reqTuple[2]), "time" : str(time.time())})
                    self.recvQ.put(dataS)
                    lRecvWaiting[i] = None
                    recvSomething = True
                    # On avertit le main thread
                    countRecvNotTransmit += 1
                    
                    
            if countRecvNotTransmit > 50 or (time.time() - countRecvTimeInit > 0.1 and countRecvNotTransmit > 0):
                countRecvNotTransmit = 0
                countRecvTimeInit = time.time()
                self.wakeUpMainThread.set()        
                    
            lRecvWaiting = filter(lambda d: not d is None, lRecvWaiting)
            if not isinstance(lRecvWaiting, list):
                lRecvWaiting = list(lRecvWaiting)

            while len(lSendWaiting) < DTM_CONCURRENT_SEND_LIMIT:
                # On envoie tous les messages
                try:
                    sendMsg = self.sendQ.get_nowait()
                    countSend += 1
                    sendMsg.sendTime = time.time()
                    commA, buf1 = self._mpiSend(sendMsg, sendMsg.receiverWid)
                    lSendWaiting.append((commA, buf1))
                    sendSomething = True
                except Queue.Empty:
                    break
            
            lSendWaiting = filter(lambda d: not d[0].Test(), lSendWaiting)
            if not isinstance(lSendWaiting, list):
                lSendWaiting = list(lSendWaiting)
            
            if not recvSomething:
                time.sleep(self.random.uniform(DTM_MPI_MIN_LATENCY, DTM_MPI_MAX_LATENCY))
                
        while len(lSendWaiting) > 0:
            # On envoie les derniers messages
            lSendWaiting = filter(lambda d: not d[0].Test(), lSendWaiting)
            if not isinstance(lSendWaiting, list):
                lSendWaiting = list(lSendWaiting)
            time.sleep(self.random.uniform(DTM_MPI_MIN_LATENCY, DTM_MPI_MAX_LATENCY))
            
        del lSendWaiting
        del lRecvWaiting
        #del MPI
        
