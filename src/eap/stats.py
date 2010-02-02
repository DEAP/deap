#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

'''The :mod:`stats` module provide a way to calculate statistics about the
:class:`~eap.observable.Observable` objects; :class:`~eap.base.Population` and
:class:`~eap.base.Individual`. It implements some basic generator functions
that receive the observed object from their :meth:`send` and return the data.

The functions provided by this module are actually bounded to a hidden instance
of class :class:`Stats`. Other instance of :class:`Stats` may be used to store
different statistics.
'''

import copy
import threading

class Stats(dict):
    '''A stats object is a dictionary that logs the statistics in a thread-safe
    environment.'''
    def __init__(self):
        self.mSemaphore = threading.Semaphore(1)

    def getStats(self, statsName):
        '''Return the current statistics that are associated with *statsName*.
        Usually, *statsName* is the name of the
        :class:`~observable.Observable` suscribed generator function.
        '''
        self.mSemaphore.acquire()
        data = self[statsName]
        self.mSemaphore.release()
        return data

    def pushStats(self, statsName, stats):
        '''Write the *stats* in the *statsName* entry of the dictionary, every
        push with the same name will replace the current value.
        '''
        self.mSemaphore.acquire()
        self[statsName] = stats
        self.mSemaphore.release()

_instance = Stats()
getStats = _instance.getStats
pushStats = _instance.pushStats


def statistics():
    '''Computes the minimum, maximum and average value of each fitness index
    of the individuals that are in the iterable population. The
    data is returned as a tuple, the first field contains the minimum, the
    second field the maximum and the third field the average.

    This function expect to receive an iterable population of individuals.
    '''
    lMin, lMax, lAvg = None, None, None
    lIndividuals = None

    while 1:
        lNewIndividuals = (yield lMin, lMax, lAvg)
        if lNewIndividuals is not None:
            lIndividuals = lNewIndividuals

        lMin = list(lIndividuals[0].mFitness[:])
        lMax = list(lIndividuals[0].mFitness[:])
        lAvg = list(lIndividuals[0].mFitness[:])

        for lInd in lIndividuals[1:]:
            for i, lMeasure in enumerate(lInd.mFitness):
                if lInd.mFitness[i] < lMin[i]:
                    lMin[i] = lInd.mFitness[i]
                elif lInd.mFitness[i] > lMax[i]:
                    lMax[i] = lInd.mFitness[i]
            
                lAvg[i] += float(lInd.mFitness[i])
        for i in range(len(lAvg)):
            lAvg[i] /= len(lIndividuals)


def bestInd():
    '''This function computes the best individual of this population and keeps
    track of the bes individual so far using the lexocigraphic comparison. The
    data is return as a tuple, the first field contains the best individual so
    far and the second field the best individual of the generation.

    This function expect to receive an iterable population of individuals.
    '''
    lBestIndividual = None
    lBestOfGeneration = None
    lIndividuals = None

    while 1:
        lNewIndividuals = yield lBestIndividual, lBestOfGeneration
        if lNewIndividuals is not None:
            lIndividuals = lNewIndividuals

        lBestOfGeneration = lIndividuals[0]
        for lInd in lIndividuals:
            if lInd.mFitness > lBestOfGeneration.mFitness:
                lBestOfGeneration = lInd
        if lBestIndividual is None or lBestOfGeneration.mFitness > lBestIndividual.mFitness:
            lBestIndividual = copy.copy(lBestOfGeneration)
        lBestOfGeneration = copy.copy(lBestOfGeneration)

class Statistics:
    def __init__(self, inList, evalStr=None):
	if evalStr == None:
	    self.evalString = 'item'
	else:
	    self.evalString = 'item.' + evalStr
	self.operations = dict()
	self.results = dict()
	self.list = inList
    def add(self, name, function):
	self.operations[name] = list((function, None))
	self.results[name] = None

    def compute(self):
	for item in self.operations.items():
	    item[1][1] = item[1][0]()
	    item[1][1].next()
	for item in self.list:
	    value = eval(self.evalString)
	    for item in self.operations.items():
		self.results[item[0]] = item[1][1].send(value)
	for item in self.operations.items():
	    item[1][1].close()
    def get(self, name):
	return self.results[name]

def max():
    max = None
    value = None
    while True:
	if value > max:
	     max = value
	value = yield max
	
def min():
    min = None
    value = None
    while True:
	if value < min or min is None:
	     min = value
	value = yield min

def mean():
    i, sum, mean = 0, 0, 0
    while True:
	value = yield mean
	sum += float(value)
	i += 1
	mean = sum / i

def variance():
    sum, sum_sq, i = 0, 0, 0
    var = 0
    while True:
	value =	yield var
	sum_sq += float(value)**2
	sum += float(value)
	i += 1
	var = (1.0/i * sum_sq - (sum/i)**2)

#def bestIndHistory():
#    lBestList = []
#
#    while 1:
#        lNewIndividuals = (yield lBestList)
#        if lNewIndividuals is not None:
#            individuals = lNewIndividuals
#
#        lBest = individuals[0].clone()
#
#        for lInd in individuals[1:]:
#
#            if lInd.isBetter(lBest):
#                lBest = lInd.clone()
#
#        lBestList.append(lBest)
        

