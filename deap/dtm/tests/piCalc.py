import sys
sys.path.append("../..")

from taskmanager import dtm

import time
import math
import random
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

def test(tries):
    return sum(math.hypot(random.random(), random.random()) < 1 for i in xrange(tries))
    
    
def calcPi(n, t):
    expr = dtm.repeat(test, n, t)
    pi2 = 4 * sum(expr) / float(n*t)
    print("pi = ", pi2)
    return pi2

piVal = dtm.start(calcPi, 2000, 5000)
