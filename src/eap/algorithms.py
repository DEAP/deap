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

'''The :mod:`algorithms` module is intended to contain some specific algorithms
in order to execute very common evolutionary algorithms. The method used here
are more for convenience than reference as the implementation of every 
evolutionary algorithm may vary infinitly. Most of the algorithms in this module
use operators registered in the toolbox with the same keywords,
:meth:`crossover` for crossover, :meth:`mutate` for mutation, :meth:`select`
for selection and :meth:`evaluate` for evaluation.

.. note::
   You are encouraged to write your own algorithms in order to make them do what
   you realy them to do.
'''

import random

def simpleEA(toolbox, population, cxPb, mutPb, nGen):
    print '-- Starting evolution --'
    # Evaluate the population
    map(toolbox.evaluate, population)
    # Begin the generational process
    for g in range(nGen):
        print '-- Generation %i --' % g

        population[:] = toolbox.select(population, n=len(population))

        # Apply crossover and mutation
        for i in xrange(1, len(population), 2):
            if random.random() < cxPb:
                population[i - 1], population[i] = toolbox.mate(population[i - 1], population[i])
        for i in xrange(len(population)):
            if random.random() < mutPb:
                population[i] = toolbox.mutate(population[i])

        # Evaluate the population
        map(toolbox.evaluate, population)

        # Gather all the fitnesses in one list and print the stats
        lFitnesses = [lInd.mFitness[0] for lInd in population]
        print '  Min %f' % min(lFitnesses)
        print '  Max %f' % max(lFitnesses)
        lSum = float(sum(lFitnesses))
        lSum2 = float(reduce(lambda x, y: x + y*y, lFitnesses, 0))
        lLenght = len(lFitnesses)
        lStdDev = ((lSum2 - (lSum*lSum / lLenght)) / (lLenght - 1))**0.5
        print '  Mean %f' % (lSum/lLenght)
        print '  Std. Dev. %f' % lStdDev

    print '-- End of evolution --'


def mupluslambdaEA(toolbox, population, lambdaFactor, nGen):
    print '-- Starting evolution --'
    # Evaluate the population
    map(toolbox.evaluate, population)
    lMuSize = len(population)
    lLambdaSize = int((lambdaFactor) * len(population))
    # Begin the generational process
    for g in range(nGen):
        print '-- Generation %i --' % g

        lNewPopulation = []
        for i in xrange(0, lLambdaSize, 3):
            lParents = toolbox.select(population, n=3)
            lNewPopulation.extend(toolbox.mate(lParents[0], lParents[1]))
            lNewPopulation.append(toolbox.mutate(lParents[2]))

        map(toolbox.evaluate, lNewPopulation)

        population.extend(lNewPopulation)
        population[:] = toolbox.select(population, n=lMuSize)

        # Gather all the fitnesses in one list and print the stats
        lFitnesses = [lInd.mFitness[0] for lInd in population]
        print '  Min %f' % min(lFitnesses)
        print '  Max %f' % max(lFitnesses)
        lSum = float(sum(lFitnesses))
        lSum2 = float(reduce(lambda x, y: x + y*y, lFitnesses, 0))
        lLenght = len(lFitnesses)
        lStdDev = ((lSum2 - (lSum*lSum / lLenght)) / (lLenght - 1))**0.5
        print '  Mean %f' % (lSum/lLenght)
        print '  Std. Dev. %f' % lStdDev

    print '-- End of evolution --'


def mucommalambdaEA(toolbox, population, lambdaFactor, nGen):
    print '-- Starting evolution --'
    # Evaluate the population
    map(toolbox.evaluate, population)
    lMuSize = len(population)
    if lambdaFactor < 1.0:
        raise ValueError, 'Lambda factor must be greater than 1.'
    lLambdaSize = int((lambdaFactor) * len(population))
    # Begin the generational process
    for g in range(nGen):
        print '-- Generation %i --' % g

        lNewPopulation = []
        for i in xrange(0, lLambdaSize, 3):
            lParents = toolbox.select(population, n=3)
            lNewPopulation.extend(toolbox.mate(lParents[0], lParents[1]))
            lNewPopulation.append(toolbox.mutate(lParents[2]))

        map(toolbox.evaluate, lNewPopulation)

        population[:] = toolbox.select(lNewPopulation, n=lMuSize)

        # Gather all the fitnesses in one list and print the stats
        lFitnesses = [lInd.mFitness[0] for lInd in population]
        print '  Min %f' % min(lFitnesses)
        print '  Max %f' % max(lFitnesses)
        lSum = float(sum(lFitnesses))
        lSum2 = float(reduce(lambda x, y: x + y*y, lFitnesses, 0))
        lLenght = len(lFitnesses)
        lStdDev = ((lSum2 - (lSum*lSum / lLenght)) / (lLenght - 1))**0.5
        print '  Mean %f' % (lSum/lLenght)
        print '  Std. Dev. %f' % lStdDev

    print '-- End of evolution --'
