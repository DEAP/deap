import sys

from deap import dtm

import time
import math
import random
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

_logger = logging.getLogger("dtm.test")

def mapFunc1(arg):
    return arg*2

def applyFunc1(arg):
    return len(arg)
    
def applyFunc2(arg):
    time.sleep(0.5)
    return arg*3
    
def applyFunc3(arg):
    return 8/arg
    
def applyFunc4(arg1, arg2, aa, bb, cc, dd):
    return (arg1+arg2+len(aa)-len(bb)+sum(cc))/float(dd+1)

def applyFunc5(arg):
    time.sleep(random.random()*3)
    return arg+1

def mapFunc2(arg):
    time.sleep(0.01)
    return arg*3

def filterFunc1(arg):
    return arg%2 == 0

def main():
    
    beginTime = time.time()
    countFailed = 0
    
    list1 = range(500)
    
    _logger.info("[%s] DTM test suite started", time.time()-beginTime)
    
    _logger.info("[%s] Testing worker id generation : '%s'", time.time()-beginTime, dtm.getWorkerId())
    
    
    _logger.info("[%s] Testing synchronous calls...", time.time()-beginTime)
    list1r = dtm.map(mapFunc1, list1)
    list1t = list(map(mapFunc1, list1))
    
    if list1r != list1t:
        _logger.warning("[%s] DTM synchronous map test FAILED!", time.time()-beginTime)
        countFailed += 1
    else:
        _logger.info("[%s] DTM synchronous map test successful", time.time()-beginTime)
    
    
    applyTestr = dtm.apply(applyFunc1, "0123456789")
    if applyTestr != 10:
        _logger.warning("[%s] DTM synchronous apply test FAILED!", time.time()-beginTime)
        countFailed += 1
    else:
        _logger.info("[%s] DTM synchronous apply test successful", time.time()-beginTime)
    
    
    repeatTestr = dtm.repeat(applyFunc1, 20, "0123456789")
    repeatTestt = [10 for i in range(20)]
    
    if repeatTestr != repeatTestt:
        _logger.warning("[%s] DTM synchronous repeat test FAILED!", time.time()-beginTime)
        countFailed += 1
    else:
        _logger.info("[%s] DTM synchronous repeat test successful", time.time()-beginTime)
        
    
    filterTestr = dtm.filter(filterFunc1, list1)
    filterTestt = list(filter(filterFunc1, list1))
    
    if filterTestr != filterTestt:
        _logger.warning("[%s] DTM synchronous filter test FAILED!", time.time()-beginTime)
        countFailed += 1
    else:
        _logger.info("[%s] DTM synchronous filter test successful", time.time()-beginTime)
    
    
    ######################################################################################
    
    _logger.info("[%s] Testing asynchronous calls...", time.time()-beginTime)
    
    timeInit = time.time()
    mapAsyncReq2 = dtm.map_async(mapFunc2, list1)
    if mapAsyncReq2.ready() and time.time() - timeInit < 0.1:
        _logger.warning("[%s] DTM asynchronous map test seems to have failed by time!", time.time()-beginTime)
    mapAsyncReq1 = dtm.map_async(mapFunc1, list1)
    
    list2t = [arg*3 for arg in list1]
    
    mapAsyncReq1.wait()
    mapAsyncReq2.wait()
    
    if list1t == mapAsyncReq1.get() and list2t == mapAsyncReq2.get():
        _logger.info("[%s] DTM asynchronous map test successful", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM asynchronous map test FAILED", time.time()-beginTime)
        countFailed += 1
    
    
    timeInit = time.time()
    applyAsyncReq1 = dtm.apply_async(applyFunc2, 1)
    if applyAsyncReq1.ready() and time.time() - timeInit < 0.5:
        _logger.warning("[%s] DTM asynchronous apply test seems to have failed by time!", time.time()-beginTime)        
    applyAsyncReq2 = dtm.apply_async(applyFunc2, 2)
    applyAsyncReq3 = dtm.apply_async(applyFunc2, 3)
    
    applyAsyncReq1.wait()
    applyAsyncReq2.wait()
    applyAsyncReq3.wait()
    
    if applyAsyncReq1.get() == 3 and applyAsyncReq2.get() == 6 and applyAsyncReq3.get() == 9:
        _logger.info("[%s] DTM asynchronous apply test successful", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM asynchronous apply test FAILED", time.time()-beginTime)
        countFailed += 1
    
    
    imapObj = dtm.imap(mapFunc1, list1)
    list3r = [i for i in imapObj]
    
    if list3r == list1t:
        _logger.info("[%s] DTM (a)synchronous imap test successful", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM (a)synchronous imap test FAILED", time.time()-beginTime)
        countFailed += 1
        
    
    imapNotOrderedObj = dtm.imap_unordered(mapFunc1, list1, 50)
    list4r = [i for i in imapNotOrderedObj]
    list4r_sorted = list(sorted(list4r))
    
    if list4r != list4r_sorted and list4r_sorted == list1t:
        _logger.info("[%s] DTM asynchronous imap_unordered test successful", time.time()-beginTime)
    elif list4r_sorted == list1t:
        _logger.info("[%s] DTM asynchronous imap_unordered MAY have failed (same behavior as imap())", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM asynchronous imap_unordered test FAILED", time.time()-beginTime)
        countFailed += 1
        
    
    ######################################################################################
    
    _logger.info("[%s] Testing asynchronous interactions...", time.time()-beginTime)
    
    mapAsyncReq2 = dtm.map_async(mapFunc2, list1)
    mapAsyncReq1 = dtm.map_async(mapFunc1, list1)
    
    if dtm.testAll([mapAsyncReq2, mapAsyncReq1]):
        _logger.warning("[%s] DTM testAll() test FAILED", time.time()-beginTime)
        countFailed += 1
    else:
        _logger.info("[%s] DTM testAll() test successful", time.time()-beginTime)
    
    
    dtm.waitAll()
    
    if mapAsyncReq1.ready() and mapAsyncReq2.ready():
        _logger.info("[%s] DTM waitAll() test successful", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM waitAll() test FAILED", time.time()-beginTime)
        countFailed += 1
    
    
    applyAsyncReq1 = dtm.apply_async(applyFunc1, "0123456789")
    mapAsyncReq2 = dtm.map_async(mapFunc2, list1)
    
    retVal = dtm.waitAny()
    if retVal == applyAsyncReq1 and applyAsyncReq1.get() == 10 and mapAsyncReq2.ready() == False:
        _logger.info("[%s] DTM waitAny() test successful", time.time()-beginTime)
    elif retVal == mapAsyncReq2 and isinstance(mapAsyncReq2.get(), list):
        _logger.info("[%s] DTM waitAny() test PROBABLY successful but weird", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM waitAny() test FAILED", time.time()-beginTime)
        countFailed += 1
    
    mapAsyncReq2.wait()
    
    if dtm.testAny() == mapAsyncReq2:
        _logger.info("[%s] DTM testAny() test successful", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM testAny() test FAILED", time.time()-beginTime)
    
    
    
    ######################################################################################
    
    _logger.info("[%s] Testing parameters and exceptions handling...", time.time()-beginTime)
    
    applyParamPassr = dtm.apply(applyFunc4, 1, 2, "abc", bb={'a':2, 'b':3, 'c':4}, cc=range(10), dd=13.37)
    applyParamPasst = applyFunc4(1, 2, "abc", bb={'a':2, 'b':3, 'c':4}, cc=range(10), dd=13.37)
    
    if applyParamPassr == applyParamPasst:
        _logger.info("[%s] DTM parameters passing test successful", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM parameters passing test FAILED", time.time()-beginTime)
        countFailed += 1
        
    
    try:
        applyExceptTestr = dtm.map(applyFunc3, [-2,-1,0])
    except ZeroDivisionError:
        _logger.info("[%s] DTM exception catch test successful", time.time()-beginTime)
    else:
        _logger.warning("[%s] DTM exception catch test FAILED", time.time()-beginTime)
        countFailed += 1
        
    
    _logger.info("[%s] DTM test suite done with %i errors", time.time()-beginTime, countFailed)
    
    return 0

#dtm.setOptions(setTraceMode=True)
dtm.start(main)

