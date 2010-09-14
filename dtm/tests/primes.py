import sys
sys.path.append("..")

from taskmanager import dtm

import time
import math


def foo(arg):
    time.sleep(0.1)
    return arg*(math.sqrt(math.pow(arg,2)))

def bar(a, b, c):
    time.sleep(0.1)
    return a+b+c


def primaryTest(nbr):
    if nbr <= 2:
        return True
        
    for i in xrange(2, int(math.sqrt(nbr))+1):
        if nbr % i == 0:
            return False
    return True

def main():
    listInit = range(150)
    print("Voici une liste :")
    print(listInit)
    print("\n")

    asyncResult1 = dtm.apply_async(bar, [1,2,3], [4,5,6,7], c = [8,9])
    weirdPow = dtm.map_async(foo, listInit)

    primes = dtm.filter(primaryTest, listInit)
    print("Voici les nombres premiers :")
    print(primes)
    print("\n")

    print("Est-ce que tous les resultats asynchrones sont prets? ", dtm.testAllAsync())
    print("Attente de tous les resultats asynchrones")
    dtm.waitForAll()
    
    print("Resultat de bar() calcule en meme temps :")
    print(asyncResult1.get())

    print("Resultat de foo() calcule en meme temps :")
    print(weirdPow.get())
    
dtm.setOptions(communicationManager="pympi")
dtm.start(main)

    