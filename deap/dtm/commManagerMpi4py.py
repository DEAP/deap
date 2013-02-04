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

from deap.dtm.dtmTypes import *
from deap.dtm.abstractCommManager import AbstractCommThread

_logger = logging.getLogger("dtm.communication")

DTM_MPI_MIN_LATENCY = 0.005
DTM_MPI_MAX_LATENCY = 0.01
DTM_CONCURRENT_RECV_LIMIT = 1000
DTM_CONCURRENT_SEND_LIMIT = 1000

class CommThread(AbstractCommThread):

    def __init__(self, recvQ, sendQ, mainThreadEvent, exitEvent, commReadyEvent, randomGenerator, cmdlineArgs):
        AbstractCommThread.__init__(self, recvQ, sendQ, mainThreadEvent, exitEvent, commReadyEvent, randomGenerator, cmdlineArgs)
        self.importErrorTrigged = False

    @property
    def poolSize(self):
        return self.pSize

    @property
    def workerId(self):
        return self.currentId

    @property
    def isRootWorker(self):
        return self.currentId == 0

    @property
    def isLaunchProcess(self):
        return False

    def setTraceModeOn(self, xmlLogger):
        self.traceMode = True
        self.traceTo = xmlLogger

    def iterOverIDs(self):
        return range(self.pSize)

    def run(self):
        try:
            from mpi4py import MPI
        except ImportError:
            _logger.error("Unable to import mpi4py. Check if the mpi4py module is in your PYTHONPATH or use a different communication manager. DTM will now exit.")
            self.commReadyEvent.set()
            self.exitStatus.set()       # Set exit at the beginning
            return

        def mpiSend(msg, dest):
            # Pickle and send over MPI
            arrayBuf = array.array('b')
            arrayBuf.fromstring(cPickle.dumps(msg, cPickle.HIGHEST_PROTOCOL))

            b = MPI.COMM_WORLD.Isend([arrayBuf, MPI.CHAR], dest=dest, tag=self.msgSendTag)
            if self.traceMode:
                etree.SubElement(self.traceTo, "msg", {"direc" : "out", "type" : str(msg.msgType), "otherWorker" : str(dest), "msgtag" : str(self.msgSendTag), "time" : repr(time.time())})

            self.msgSendTag += 1
            return b, arrayBuf

        self.pSize = MPI.COMM_WORLD.Get_size()
        self.currentId = MPI.COMM_WORLD.Get_rank()

        MPI.COMM_WORLD.Barrier()

        self.commReadyEvent.set()   # Notify the main thread that we are ready

        if self.currentId == 0 and MPI.Query_thread() > 0:
            # Warn only once
            _logger.warning("MPI was initialized with a thread level of %i, which is higher than MPI_THREAD_SINGLE."
            " The current MPI implementations do not always handle well the MPI_THREAD_MULTIPLE or MPI_THREAD_SERIALIZED modes."
            " As DTM was designed to work with the base, safe mode (MPI_THREAD_SINGLE), it is strongly suggested to change"
            " the 'thread_level' variable or your mpi4py settings in 'site-packages/mpi4py/rc.py', unless you have strong"
            " motivations to keep that setting. This may bring both stability and performance improvements.", MPI.Query_thread())

        lRecvWaiting = []
        lSendWaiting = []
        countSend = 0
        countRecv = 0
        lMessageStatus = MPI.Status()
        working = True

        countRecvNotTransmit = 0
        countRecvTimeInit = time.time()

        while working:
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # Exiting
                # Warning : the communication thread MUST clear the sendQ
                # BEFORE leaving (the exiting orders must be send)
                working = False

            while len(lRecvWaiting) < DTM_CONCURRENT_RECV_LIMIT and MPI.COMM_WORLD.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=lMessageStatus):
                # We received something
                lBuf = array.array('b', (0,))
                lBuf = lBuf * lMessageStatus.Get_elements(MPI.CHAR)

                lRecvWaiting.append((lBuf, MPI.COMM_WORLD.Irecv([lBuf, MPI.CHAR], source=lMessageStatus.Get_source(), tag=lMessageStatus.Get_tag()), lMessageStatus.Get_tag()))

                lMessageStatus = MPI.Status()
                recvSomething = True


            for i, reqTuple in enumerate(lRecvWaiting):
                if reqTuple[1].Test():
                    countRecv += 1
                    dataS = cPickle.loads(reqTuple[0].tostring())
                    if self.traceMode:
                        etree.SubElement(self.traceTo, "msg", {"direc" : "in", "type" : str(dataS.msgType), "otherWorker" : str(dataS.senderWid), "msgtag" : str(reqTuple[2]), "time" : repr(time.time())})
                    self.recvQ.put(dataS)
                    lRecvWaiting[i] = None
                    recvSomething = True
                    # Wake up the main thread if there's a sufficient number
                    # of pending receives
                    countRecvNotTransmit += 1


            if countRecvNotTransmit > 50 or (time.time() - countRecvTimeInit > 0.1 and countRecvNotTransmit > 0):
                countRecvNotTransmit = 0
                countRecvTimeInit = time.time()
                self.wakeUpMainThread.set()

            lRecvWaiting = filter(lambda d: not d is None, lRecvWaiting)

            while len(lSendWaiting) < DTM_CONCURRENT_SEND_LIMIT:
                # Send all pending sends, under the limit of
                # DTM_CONCURRENT_SEND_LIMIT
                try:
                    sendMsg = self.sendQ.get_nowait()
                    countSend += 1
                    sendMsg.sendTime = time.time()
                    commA, buf1 = mpiSend(sendMsg, sendMsg.receiverWid)
                    lSendWaiting.append((commA, buf1))
                    sendSomething = True
                except Queue.Empty:
                    break

            lSendWaiting = filter(lambda d: not d[0].Test(), lSendWaiting)

            if not recvSomething:
                time.sleep(self.random.uniform(DTM_MPI_MIN_LATENCY, DTM_MPI_MAX_LATENCY))

        while len(lSendWaiting) > 0:
            # Send the lasts messages before shutdown
            lSendWaiting = filter(lambda d: not d[0].Test(), lSendWaiting)
            time.sleep(self.random.uniform(DTM_MPI_MIN_LATENCY, DTM_MPI_MAX_LATENCY))

        del lSendWaiting
        del lRecvWaiting
