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

DTM_TASK_STATE_IDLE = 0
DTM_TASK_STATE_RUNNING = 1
DTM_TASK_STATE_WAITING = 2
DTM_TASK_STATE_FINISH = 3

DTM_MSG_EXIT = 0
DTM_MSG_TASK = 1
DTM_MSG_REQUEST_TASK = 2
DTM_MSG_RESULT = 3
DTM_MSG_ACK_RECEIVED_TASK = 4

DTM_WAIT_NONE = 0
DTM_WAIT_SOME = 1
DTM_WAIT_ALL = 2
DTM_WAIT_ANY = 3

class DtmTaskContainer(object):
    """
    Contains all the information about a task (running or not)
    """
    __slots__ = ('tid', # Unique ID of the task
                'creatorWid', # ID of the worker who creates this task
                'creatorTid', # ID of the task who creates this task (parent)
                'taskIndex', # Position into the parents task childs list
                'taskRoute', # Worker path followed by the job before begin
                'creationTime', # Time at the job creation
                'target', # Target function (or callable object) of the task
                'args', # Arguments (list)
                'kwargs', # Key-worded arguments (dictionnary)
                'threadObject', # Python representation of the thread
                'taskState')    # State of the task (DTM_TASK_*)
    def __init__(self, args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self, state):
        for t in state:
            self.__setattr__(t, state[t])
    def __lt__(self, other):
        return self.creationTime < other.creationTime

class DtmResultContainer(object):
    """
    Used to store the result of a task so it can be sent
    """
    __slots__ = ('tid', # ID of the task which produced these results
                'parentTid', # Parent ID (waiting for these results)
                'taskIndex', # Position into the parents task childs list
                'execTime', # Total execution time (NOT waiting time)
                'success', # False if an exception occured
                'result')       # The result; if an exception occured, contains it
    def __init__(self, args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self, state):
        for t in state:
            self.__setattr__(t, state[t])

class DtmExceptedResultContainer(object):
    """
    Keep the information of a result waited on the task creator side
    """
    __slots__ = ('tids', # List of IDs of the tasks which produce these results
                'waitingOn', # Is the parent task waiting on this result?
                'finished', # Boolean : is the task finished (i.e. result received)?
                'success', # Boolean : False if unfinished or if an exception occured
                'callbackFunc', # Callback function, FOR USE IN DTM, NO ARGUMENTS PASSED, or None
                'result')       # Result, or the exception occured
    def __init__(self, args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self, state):
        for t in state:
            self.__setattr__(t, state[t])
            
class DtmWaitInfoContainer(object):
    """
    Keep a track on the pending child tasks of a parent task.
    """
    __slots__ = ('threadObject', # Python representation of the thread
                'eventObject', # threading.Event flag (to wake up the thread)
                'waitBeginningTime', # Time when the thread started waiting (0 if not)
                'tasksWaitingCount', # How many tasks are we waiting on
                'waitingMode', # DTM_WAIT_* : waiting mode (None, One, Any, All)
                'rWaitingDict')     # List of DtmExceptedResultContainer, key : the first task ID
    def __init__(self, args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self, state):
        for t in state:
            self.__setattr__(t, state[t])

class DtmStatsContainer(object):
    """
    Contains stats about a target
    """
    __slots__ = ('rAvg', # RELATIVE average execution time
                'rStdDev', # RELATIVE standard deviation of the exec time
                'rSquareSum', # Square sum of the RELATIVE exec times
                'execCount')    # Number of executions
    def __init__(self, args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self, state):
        for t in state:
            self.__setattr__(t, state[t])

class DtmMessageContainer(object):
    """
    Generic message container
    If msgType == DTM_MSG_EXIT:
        msg = (Exit code, exit message)
    If msgType == DTM_MSG_TASK:
        msg = [DtmTaskContainer, DtmTaskContainer, DtmTaskContainer, ...]
    If msgType == DTM_MSG_REQUEST_TASK:
        msg = None
    If msgType == DTM_MSG_RESULT:
        msg = [DtmResultContainer, DtmResultContainer, DtmResultContainer, ...]
    If msgType == DTM_MSG_ACK_RECEIVED_TASK:
        msg = AckId
    """
    __slots__ = ('msgType', # Message type (DTM_MSG_*)
                'senderWid', # Worker id of the sender
                'receiverWid', # Worker id of the receiver
                'loadsDict', # Load dictionnary of the sender
                'targetsStats', # Stats on the tasks of the sender
                'prepTime', # Time when it was ready to send
                'sendTime', # Time when sent
                'ackNbr', # ACK number (optionnal for some operations)
                'msg')          # Message (varies with msgType)
    def __init__(self, args):
        self.__setstate__(args)    
    def __getstate__(self):
        d = {}
        for a in self.__slots__:
            d[a] = self.__getattribute__(a)
        return d    
    def __setstate__(self, state):
        for t in state:
            self.__setattr__(t, state[t])
            
