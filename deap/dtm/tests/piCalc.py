
from math import hypot
from random import random

from deap import dtm

def test(tries):
    return sum(hypot(random(), random()) < 1 for i in xrange(tries))
    
    
def calcPi(n, t):
    expr = dtm.repeat(test, n, t)
    pi2 = 4. * sum(expr) / float(n*t)
    print("pi = " + str(pi2))
    return pi2

dtm.start(calcPi, 2000, 5000)