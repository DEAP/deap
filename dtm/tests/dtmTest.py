import sys
sys.path.append("..")

from taskmanager import dtm

import time
import math
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

def reboum(c):
    return c-100+22-math.sqrt(12)

def boumtest(a):
    print("\t\t1\t\t\t" + str(dtm.getWorkerId()))
    time.sleep(0.1)
    return a.getTruc()*a.getTruc()-a.getTruc()+math.sqrt(a.getTruc())*math.sqrt(a.getTruc())

def boumtest2(b):
    print("\t\t\t2\t\t" + str(dtm.getWorkerId()))
    time.sleep(0.1)
    listK = [b for i in xrange(30)]
    newList = dtm.map(reboum, listK)
    return b+b-b*b+b*b - newList[5]

def boumtest3(b):
    print("\t\t\t\t3\t" + str(dtm.getWorkerId()))
    time.sleep(0.1)
    return b+b + math.sqrt(b)

class TrucChose(object):

    def __init__(self,a):
        self.a = a
        self.boumTruc = {}
        self.patatras = [1,2]

    def getTruc(self):
        return self.a

def applyTest(a,b,c):
    time.sleep(0.5)
    return a + b + c

def main():
    print("\tMain started")
    befTime = time.time()

    w = dtm.apply_async(applyTest, 15, b = 30, c = 45)
    print("Async return!")
    w.wait()
    
    r = dtm.apply_async(applyTest, [1,2,3], [4,5,6], c = [7,8,9])
    print("APPLY RESULT ", r)

    print("Is async done?", dtm.testAllAsync())

    print("BEFORE WAIT FOR ALL")
    fTime = time.time()
    dtm.waitForAll()
    print("AFTER WAIT FOR ALL ", time.time()-fTime)
    print("Is async done?", dtm.testAllAsync())
   
    print(r.get())
    print(w.get())

    listT = [TrucChose(i) for i in xrange(25)]
    listW = dtm.map_async(boumtest, listT)
    listK = dtm.map_async(boumtest3, [i for i in xrange(14)])
    #print("BOUM!")
    listZ = dtm.imap(boumtest2, [i for i in xrange(10)], 4)
    
    print("YEAH")
    listW.wait()
    print(listW.get())
    for z in listZ:
        print(z)
    print("\tMain resumed after " + str(time.time()-befTime))
    return 0

dtm.setOptions(communicationManager="mpi4py")
dtm.start(main)

