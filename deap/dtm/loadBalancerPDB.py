#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

import threading
try:
    import Queue
except ImportError:
    import queue as Queue
import time
import copy
import logging

from collections import defaultdict

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        # Python 2.5
        import xml.etree.ElementTree as etree

_logger = logging.getLogger("dtm.loadBalancing")


DTM_ASK_FOR_TASK_DELAY = 2.5
DTM_SEND_TASK_DELAY = 0.001
DTM_RESTART_QUEUE_BLOCKING_FROM = 1.

class LoadInfoContainer(object):
    """
    Contains load information of a worker
    """
    __slots__ = ('loadCurrentExec',     # Load of the current exec task
                'loadExecQ',            # Load of the exec queue
                'loadWaitingRestartQ',  # Load of the waiting for restart queue
                'loadWaitingQ',         # Load of the waiting queue
                'seqNbr',               # Sequence number, only ++ by the worker which is its info
                'infoUpToDate',         # Boolean : is the dictionnary of the OTHER worker up to date with our info?
                'ackWaiting')           # List of ACKs (messages transmitted)
    def __init__(self,args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self,state):
        for t in state:
            self.__setattr__(t,state[t])
    def sumRealLoad(self):
        return self.loadCurrentExec+self.loadExecQ+self.loadWaitingRestartQ

class LoadBalancer(object):
    """
    """
    def __init__(self, workersIterator, workerId, execQueue, randomizer):
        self.wid = workerId
        self.ws = {}
        self.execQ = execQueue      # Les autres queues ne sont pas necessaires
        self.wIter = workersIterator
        self.dLock = threading.Lock()
        self.tmpRecvJob = False
        self.localRandom = randomizer
        self.xmlLogger = None

        for w in workersIterator:
            self.ws[w] = LoadInfoContainer({'loadCurrentExec' : 0.,
                                            'loadExecQ' : 0.,
                                            'loadWaitingRestartQ' : 0.,
                                            'loadWaitingQ' : 0.,
                                            'seqNbr' : 0.,
                                            'infoUpToDate' : False,
                                            'ackWaiting' : []})

        self.totalExecLoad, self.totalEQueueLoad, self.totalWaitingRQueueLoad, self.totalWaitingQueueLoad = 0., 0., 0., 0.
        self.sendDelayMultiplier = DTM_SEND_TASK_DELAY*float(len(self.ws))**0.5
        self.lastTaskSend = time.time() - self.sendDelayMultiplier
        self.lastQuerySend = time.time()
        
        self.randomizedWorkersList = [w for w in self.wIter]
        randomizer.shuffle(self.randomizedWorkersList)
    
    def setTraceModeOn(self, xmlLogger):
        self.xmlLogger = xmlLogger
    
    def getNodesDict(self):
        return self.ws

    def updateSelfStatus(self, statusTuple):
        self.ws[self.wid].loadCurrentExec = statusTuple[0]
        self.ws[self.wid].loadExecQ = statusTuple[1]
        self.ws[self.wid].loadWaitingRestartQ = statusTuple[2]
        self.ws[self.wid].loadWaitingQ = statusTuple[3]       
        self.ws[self.wid].seqNbr += 1

    def mergeNodeStatus(self, otherDict):
        return
    
    def notifyTaskReceivedFrom(self, fromId):
        self.ws[fromId].infoUpToDate = True
        self.tmpRecvJob = True

    def acked(self, fromWorker, ackN):
        try:
            self.ws[fromWorker].ackWaiting.remove(ackN)
        except ValueError:
            print("ERROR : Tentative to delete an already received or non-existant ACK!", self.ws[fromWorker].ackWaiting, ackN)

    def takeDecision(self):
        sendTasksList = []
        checkedTasksNbr = 0
        sendTmpDict = defaultdict(list)
        while self.execQ.getLen() > 1 and checkedTasksNbr < self.execQ.getLen():
            # We only send a task if we are its creator
            # Round-robin task assignation to other workers
            for worker in self.randomizedWorkersList:
                if self.execQ.getLen() <= 1:
                    break
                if not worker == self.wid:
                    while checkedTasksNbr < self.execQ.getLen():
                        checkedTasksNbr += 1
                        try:
                            tObj = self.execQ.getTask()
                        except Queue.Empty:
                            break
                        if tObj.creatorWid == self.wid:
                            sendTmpDict[worker].append(tObj)
                            break
                        else:
                            self.execQ.put(tObj)
                    
        for widToSend in self.randomizedWorkersList:
            if len(sendTmpDict[widToSend]) == 0:
                continue
            ackNbr = len(self.ws[widToSend].ackWaiting)
            self.ws[widToSend].ackWaiting.append(ackNbr)
            sendTasksList.append((widToSend, sendTmpDict[widToSend], ackNbr))
        return [], sendTasksList