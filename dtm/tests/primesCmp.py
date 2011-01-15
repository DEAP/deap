import sys
sys.path.append("..")

import random
random.seed(12)

from taskmanager import dtm

import time
import math


def foo(arg):
    return arg*(math.sqrt(math.pow(arg,2)))

def bar(a, b, c):
    time.sleep(0.1)
    return a+b+c


def primaryTest(nbr):
#    print(nbr)
    if nbr <= 2:
        return True
    
    #time.sleep(25)
    for i in xrange(2, int(math.sqrt(nbr))+1):
        if nbr % i == 0:
            return False
#    a = dtm.apply(foo, 3)
    return True

def main():
	t = time.time()
	listNbr = range(3,75003,2)
	print("BOUM")
	listPrimes = dtm.filter(primaryTest, listNbr)
	print("NBR : ", len(listPrimes))
	print("Duree : " + str(time.time()-t))
#	time.sleep(10)
#	for i in listNbr:
#		i = i+0
#	a = dtm.apply(foo,3)
#	print(a,"END")
	time.sleep(1)
	
dtm.setOptions(communicationManager="mpi4py")
dtm.start(main)
