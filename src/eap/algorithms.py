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

def simpleGA(toolbox, population, cxPb, mutPb, nGen):
    # Evaluate the population
    map(toolbox.evaluate, population)
    # Begin the evolution
    for g in range(nGen):
        print 'Generation', g

        population[:] = toolbox.select(population, n=len(population))

        # Apply crossover and mutation
        for i in xrange(1, len(population), 2):
            if random.random() < cxPb:
                population[i - 1], population[i] = toolbox.crossover(population[i - 1], population[i])
        for i in xrange(len(population)):
            if random.random() < mutPb:
                population[i] = toolbox.mutate(population[i])

        # Evaluate the population
        map(toolbox.evaluate, population)

        # Gather all the fitnesses in one list and print the stats
        lFitnesses = [lInd.mFitness[0] for lInd in population]
        print '\tMin Fitness :', min(lFitnesses)
        print '\tMax Fitness :', max(lFitnesses)
        print '\tMean Fitness :', sum(lFitnesses)/len(lFitnesses)

    print 'End of evolution'
