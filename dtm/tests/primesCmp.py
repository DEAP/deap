import sys
sys.path.append("..")

from taskmanager import dtm

import time
import math


def foo(arg):
    return arg*(math.sqrt(math.pow(arg,2)))

def bar(a, b, c):
    time.sleep(0.1)
    return a+b+c


def primaryTest(nbr):
    if nbr <= 2:
        return True
    
    #time.sleep(25)
    for i in xrange(2, int(math.sqrt(nbr))+1):
        if nbr % i == 0:
            return False
    return True

def main():
	t = time.time()
	listNbr = range(3,2003,2)
	print("BOUM")
	listPrimes = dtm.filter(primaryTest, listNbr)
	print("NBR : ", len(listPrimes))
	print("Duree : " + str(time.time()-t))
	
dtm.setOptions(communicationManager="multiprocTCP")
dtm.start(main)
