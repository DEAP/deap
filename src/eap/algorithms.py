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

'''The :mod:`creator` module is an helper module in order to simplify the
object creation. Its one and only purpose is to register some function that can
be called as generator in populations' and individuals' *generator* argument.
The creator is responsible of intanciating the objects needed by the algorithms.
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
