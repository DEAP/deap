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

"""The :mod:`algorithms` module is intended to contain some specific algorithms
in order to execute very common evolutionary algorithms. The method used here
are more for convenience than reference as the implementation of every 
evolutionary algorithm may vary infinitly. Most of the algorithms in this module
use operators registered in the toolbox with the same keywords,
:meth:`mate` for crossover, :meth:`mutate` for mutation, :meth:`~eap.select`
for selection and :meth:`evaluate` for evaluation.

You are encouraged to write your own algorithms in order to make them do what
you realy them to do.
"""

import logging
import math
import random

_logger = logging.getLogger("eap.algorithms")

def eaSimple(toolbox, population, cxpb, mutpb, ngen, halloffame=None):
    """This algorithm reproduce the simplest evolutionary algorithm.
       
    """
    _logger.info("Start of evolution")
    evaluations = 0
    
    # Evaluate the individuals with invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            evaluations += 1
            ind.fitness.values = toolbox.evaluate(ind)
    
    _logger.debug("Evaluated %i individuals", evaluations)
    
    try:
        halloffame.update(population)
    except AttributeError:
        pass
    
    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        evaluations = 0
        
        # Select the next generation individuals
        population[:] = toolbox.select(population, n=len(population))

        # Apply crossover and mutation
        for i in xrange(1, len(population), 2):
            if random.random() < cxpb:
                population[i - 1], population[i] = \
                    toolbox.mate(population[i - 1], population[i])
        for i in xrange(len(population)):
            if random.random() < mutpb:
                population[i] = toolbox.mutate(population[i])

        # Evaluate the individuals with invalid fitness
        for ind in population:
            if not ind.fitness.valid:
                evaluations += 1
                ind.fitness.values = toolbox.evaluate(ind)
        
        _logger.debug("Evaluated %i individuals", evaluations)
                
        try:
            halloffame.update(population)
        except AttributeError:
            pass

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in population]
        _logger.debug("Min %f", min(fits))
        _logger.debug("Max %f", max(fits))
        lenght = len(population)
        mean = sum(fits) / lenght
        sum2 = sum(map(lambda x: x**2, fits))
        std_dev = abs(sum2 / lenght - mean**2)**0.5
        _logger.debug("Mean %f", mean)
        _logger.debug("Std. Dev. %f", std_dev)

    _logger.info("End of (successful) evolution")

def eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen, halloffame=None):
    """This is the :math:`(\mu + \lambda)` evolutionary algorithm, ...
    """
    assert (cxpb + mutpb) <= 1.0, "The sum of the crossover and mutation probabilities must be smaller or equal to 1.0."
    
    _logger.info("Start of evolution")
    evaluations = 0
    
    # Evaluate the individuals with invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            evaluations += 1
            ind.fitness.values = toolbox.evaluate(ind)
    
    _logger.debug("Evaluated %i individuals", evaluations)
            
    try:
        halloffame.update(population)
    except AttributeError:
        pass
    
    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        evaluations = 0
        
        children = []
        for i in xrange(lambda_):
            op_choice = random.random()
            if op_choice < cxpb:            # Apply crossover
                p1, p2 = random.sample(population, 2)
                children.append(toolbox.mate(p1, p2)[0])    # Only the first child is selected
            elif op_choice < cxpb + mutpb:  # Apply mutation
                p = random.choice(population)
                children.append(toolbox.mutate(p))
            else:                           # Apply reproduction
                children.append(random.choice(population))
        
        # Evaluate the individuals with invalid fitness
        for ind in children:
            if not ind.fitness.valid:
                evaluations += 1
                ind.fitness.values = toolbox.evaluate(ind)
        
        _logger.debug("Evaluated %i individuals", evaluations)
        
        try:
            halloffame.update(children)
        except AttributeError:
            pass
            
        population[:] = toolbox.select(population + children, mu)
        
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in population]
        _logger.debug("Min %f", min(fits))
        _logger.debug("Max %f", max(fits))
        lenght = len(population)
        mean = sum(fits) / lenght
        sum2 = sum(map(lambda x: x**2, fits))
        std_dev = abs(sum2 / lenght - mean**2)**0.5
        _logger.debug("Mean %f", mean)
        _logger.debug("Std. Dev. %f", std_dev)

    _logger.info("End of (successful) evolution")
    
def eaMuCommaLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen, halloffame=None):
    """This is the :math:`(\mu~,~\lambda)` evolutionary algorithm
    """
    assert lambda_ >= mu, "lambda must be greater or equal to mu." 
    assert (cxpb + mutpb) <= 1.0, "The sum of the crossover and mutation probabilities must be smaller or equal to 1.0."
        
    _logger.info("Start of evolution")
    evaluations = 0
    
    # Evaluate the individuals with invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            evaluations += 1
            ind.fitness.values = toolbox.evaluate(ind)
    
    _logger.debug("Evaluated %i individuals", evaluations)
            
    try:
        halloffame.update(population)
    except AttributeError:
        pass
    
    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        evaluations = 0
        
        children = []
        for i in xrange(lambda_):
            op_choice = random.random()
            if op_choice < cxpb:            # Apply crossover
                p1, p2 = random.sample(population, 2)
                children.append(toolbox.mate(p1, p2)[0])    # Only the first child is selected
            elif op_choice < cxpb + mutpb:  # Apply mutation
                p = random.choice(population)
                children.append(toolbox.mutate(p))
            else:                           # Apply reproduction
                children.append(random.choice(population))
        
        # Evaluate the individuals with invalid fitness
        for ind in children:
            if not ind.fitness.valid:
                evaluations += 1
                ind.fitness.values = toolbox.evaluate(ind)
        
        _logger.debug("Evaluated %i individuals", evaluations)
        
        try:
            halloffame.update(children)
        except AttributeError:
            pass
        
        population[:] = toolbox.select(children, mu)

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in population]
        _logger.debug("Min %f", min(fits))
        _logger.debug("Max %f", max(fits))
        lenght = len(population)
        mean = sum(fits) / lenght
        sum2 = sum(map(lambda x: x**2, fits))
        std_dev = abs(sum2 / lenght - mean**2)**0.5
        _logger.debug("Mean %f", mean)
        _logger.debug("Std. Dev. %f", std_dev)

    _logger.info("End of (successful) evolution")
    
def eaSteadyState(toolbox, population, ngen, halloffame=None):
    """The is the steady-state evolutionary algorithm
    """
    _logger.info("Start of evolution")
    
    # Evaluate the individuals with an invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            ind.fitness.extend(toolbox.evaluate(ind))
    
    try:
        halloffame.update(population)
    except AttributeError:
        pass
    
    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        
        p1, p2 = toolbox.select(population, 2)
        child = toolbox.mate(p1, p2)[0]     # Only the first child is selected
        child = toolbox.mutate(child)
        
        if not child.fitness.valid:
            child.fitness.extend(toolbox.evaluate(child))
        
        try:
            halloffame.update([child])
        except AttributeError:
            pass
        
        population.append(child)
        
        population[:] = toolbox.select(population, len(population) - 1)
        
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in population]
        _logger.debug("Min %f", min(fits))
        _logger.debug("Max %f", max(fits))
        lenght = len(population)
        mean = sum(fits) / lenght
        sum2 = sum(map(lambda x: x**2, fits))
        std_dev = abs(sum2 / lenght - mean**2)**0.5
        _logger.debug("Mean %f", mean)
        _logger.debug("Std. Dev. %f", std_dev)

    _logger.info("End of (successful) evolution")

