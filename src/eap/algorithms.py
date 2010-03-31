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
:meth:`mate` for crossover, :meth:`mutate` for mutation, :meth:`~eap.select`
for selection and :meth:`evaluate` for evaluation.

You are encouraged to write your own algorithms in order to make them do what
you realy them to do.
'''

from itertools import imap
import logging
import math
import random

_logger = logging.getLogger('eap.algorithms')

def simpleEA(toolbox, population, cxpb, mutpb, ngen):
    '''The simpleEA algorithm ...
    '''
    _logger.info("Start of evolution")
    # Evaluate the population
    map(toolbox.evaluate, population)
    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)

        population[:] = toolbox.select(population, n=len(population))

        # Apply crossover and mutation
        for i in xrange(1, len(population), 2):
            if random.random() < cxpb:
                population[i - 1], population[i] = toolbox.mate(population[i - 1], population[i])
        for i in xrange(len(population)):
            if random.random() < mutpb:
                population[i] = toolbox.mutate(population[i])

        # Evaluate the population
        map(toolbox.evaluate, population)

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness[0] for ind in population]
        _logger.debug("Min %f", min(fits))
        _logger.debug("Max %f", max(fits))
        lenght = len(population)
        mean = sum(fits) / lenght
        sum2 = sum(imap(lambda x: x**2, fits))
        std_dev = (sum2 / lenght - mean**2)**0.5
        _logger.debug("Mean %f", mean)
        _logger.debug("Std. Dev. %f", std_dev)

    _logger.info("End of (successful) evolution")

