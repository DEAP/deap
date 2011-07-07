import threading

from abc import ABCMeta, abstractmethod, abstractproperty

class AbstractCommThread(threading.Thread):
    __metaclass__ = ABCMeta

    def __init__(self, recvQ, sendQ, mainThreadEvent, exitEvent, commReadyEvent, randomGenerator, cmdlineArgs):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        
        self.exitStatus = exitEvent
        self.msgSendTag = 2
        self.wakeUpMainThread = mainThreadEvent
        self.random = randomGenerator
        self.commReadyEvent = commReadyEvent
        
        self.cmdArgs = cmdlineArgs
        
        self.traceMode = False
        self.traceTo = None
    
    @abstractproperty
    def poolSize(self):
        """
        Return the number of effective workers (for instance, with MPI, this
        is the number of slots asked with the -n or -np option)
        """
        pass

    @abstractproperty
    def workerId(self):
        """
        Return an ID for this worker such as each worker gets a different ID.
        This must be an immutable type (int, string, tuple, etc.)
        """
        pass

    @abstractproperty
    def isRootWorker(self):
        """
        Return True if this worker is the "root worker", that is the worker
        which will start the main task. The position of this worker in the
        hosts is not important, but one and only one worker should be
        designated as the root worker (the others should receive False).
        """
        pass
    
    @abstractproperty
    def isLaunchProcess(self):
        """
        If this function returns True, the main thread will wait for the
        termination of this thread, and then exit without executing any
        task. This may be useful for the backends which have to launch
        themselves the remote DTM processes.
        """
        pass
    
    @abstractmethod
    def setTraceModeOn(self, xmlLogger):
        """
        Used for logging purposes. The xmlLogger arg is an xml.etree object
        which can be use by the backend to log some informations. The log
        format is not currently specified, and the backend may choose to
        ignore this call (and not log anything).
        """
        pass
    
    @abstractmethod
    def iterOverIDs(self):
        """
        Return an iterable over all the worker IDs. For instance, if your
        workers IDs are integers between 0 and 63, it should then return
        range(0,64). 
        """
        pass
    
    @abstractmethod
    def run(self):
        """
        The main method, which will be call to start the communication backend.
        This is the place where you should import your special modules, and
        insert the communication loop.
        """
        pass
        