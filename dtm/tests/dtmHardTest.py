 
import sys
sys.path.append("..")

import random
random.seed(12)

from taskmanager import dtm

import time
import math

RECURSIVITY_LEVEL = 13

def foo(arg):
    return arg*(math.sqrt(math.pow(arg,2)))

def bar(a, b, c):
    time.sleep(0.1)
    return a+b+c

def recursiveFunc(level):
    if level == 1:
        #time.sleep(0.01)
        #return dtm.apply(foo, 1)
        return 1
    else:
        args = [level-1] * 2
        s = sum(dtm.map(recursiveFunc, args))
        if level >= RECURSIVITY_LEVEL:
            print(s)
        return s

    
dtm.setOptions(communicationManager="mpi4py")
dtm.start(recursiveFunc, RECURSIVITY_LEVEL)
