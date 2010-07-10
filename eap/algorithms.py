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
you realy want them to do.
"""

import copy
import logging
import random

_logger = logging.getLogger("eap.algorithms")

def eaSimple(toolbox, population, cxpb, mutpb, ngen, halloffame=None):
    """This algorithm reproduce the simplest evolutionary algorithm as
    presented in chapter 7 of Back, Fogel and Michalewicz,
    "Evolutionary Computation 1 : Basic Algorithms and Operators", 2000.
    It uses :math:`\lambda = \kappa = \mu` and goes as
    follow. It first initializes the population (:math:`P(0)`) by evaluating
    every individual presenting an invalid fitness. Then, it enters the
    evolution loop that begins by mating a proportion of the population
    determined by *cxpb* and placing the resulting individuals in
    :math:`P'(g)`, the other individuals are transfered as is in :math:`P'(g)`.
    Thereafter, a proportion of :math:`P'(g)`, determined by *mutpb*, is 
    mutated and placed in :math:`P''(g)`, the untouched individuals are
    transfered :math:`P''(g)`. Finally, the new individuals are evaluated
    and the selection occurs in :math:`P''(g)` in order to generate
    :math:`P(g + 1)`. The evolution loop continues until *ngen* generations
    are completed.
    """
    _logger.info("Start of evolution")
    evaluations = 0

    # Evaluate the individuals with invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            evaluations += 1
            ind.fitness.values = toolbox.evaluate(ind)

    _logger.debug("Evaluated %i individuals", evaluations)

    if halloffame is not None:
        halloffame.update(population)

    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        evaluations = 0

        # Apply crossover and mutation
        for i in xrange(1, len(population), 2):
            if random.random() < cxpb:
                population[i - 1], population[i] = \
                    toolbox.mate(population[i - 1], population[i])
        for i in xrange(len(population)):
            if random.random() < mutpb:
                population[i], = toolbox.mutate(population[i])

        # Evaluate the individuals with invalid fitness
        for ind in population:
            if not ind.fitness.valid:
                evaluations += 1
                ind.fitness.values = toolbox.evaluate(ind)

        _logger.debug("Evaluated %i individuals", evaluations)

        if halloffame is not None:
            halloffame.update(population)
        
        # Select the next generation population
        population[:] = toolbox.select(population, n=len(population))

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values for ind in population]
        fits_t = zip(*fits)             # Transpose fitnesses for analysis

        minimums = map(min, fits_t)
        maximums = map(max, fits_t)
        lenght = len(population)
        sums = map(sum, fits_t)
        sums2 = [sum(map(lambda x: x**2, fit)) for fit in fits_t]
        means = [sum_ / lenght for sum_ in sums]
        std_devs = [abs(sum2 / lenght - mean**2)**0.5 for sum2, mean in zip(sums2, means)]

        _logger.debug("Min %s", ", ".join(map(str, minimums)))
        _logger.debug("Max %s", ", ".join(map(str, maximums)))
        _logger.debug("Avg %s", ", ".join(map(str, means)))
        _logger.debug("Std %s", ", ".join(map(str, std_devs)))

    _logger.info("End of (successful) evolution")

def eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen, halloffame=None):
    """This is the :math:`(\mu + \lambda)` evolutionary algorithm, ...
    """
    assert (cxpb + mutpb) <= 1.0, ("The sum of the crossover and mutation"
        "probabilities must be smaller or equal to 1.0.")
    
    _logger.info("Start of evolution")
    evaluations = 0

    # Evaluate the individuals with invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            evaluations += 1
            ind.fitness.values = toolbox.evaluate(ind)

    _logger.debug("Evaluated %i individuals", evaluations)

    if halloffame is not None:
        halloffame.update(population)

    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        evaluations = 0

        offsprings = []
        nb_offsprings = 0
        while nb_offsprings < lambda_:
        #for i in xrange(lambda_):
            op_choice = random.random()
            if op_choice < cxpb:            # Apply crossover
                p1, p2 = random.sample(population, 2)
                children = toolbox.mate(p1, p2)
                offsprings.extend(children)
                nb_offsprings += len(children)
            elif op_choice < cxpb + mutpb:  # Apply mutation
                p = random.choice(population)
                mutants = toolbox.mutate(p)
                offsprings.extend(mutants)
                nb_offsprings += len(mutants)
            else:                           # Apply reproduction
                offsprings.append(random.choice(population))
                nb_offsprings += 1
        
        # Remove the exedant of offsprings
        if nb_offsprings > lambda_:
            del offsprings[lambda_:]

        # Evaluate the individuals with invalid fitness
        for ind in offsprings:
            if not ind.fitness.valid:
                evaluations += 1
                ind.fitness.values = toolbox.evaluate(ind)

        _logger.debug("Evaluated %i individuals", evaluations)

        if halloffame is not None:
            halloffame.update(offsprings)

        # Select the next generation population
        population[:] = toolbox.select(population + offsprings, mu)

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values for ind in population]
        fits_t = zip(*fits)             # Transpose fitnesses for analysis

        minimums = map(min, fits_t)
        maximums = map(max, fits_t)
        lenght = len(population)
        sums = map(sum, fits_t)
        sums2 = [sum(map(lambda x: x**2, fit)) for fit in fits_t]
        means = [sum_ / lenght for sum_ in sums]
        std_devs = [abs(sum2 / lenght - mean**2)**0.5 for sum2, mean in zip(sums2, means)]

        _logger.debug("Min %s", ", ".join(map(str, minimums)))
        _logger.debug("Max %s", ", ".join(map(str, maximums)))
        _logger.debug("Avg %s", ", ".join(map(str, means)))
        _logger.debug("Std %s", ", ".join(map(str, std_devs)))

    _logger.info("End of (successful) evolution")
    
def eaMuCommaLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen, halloffame=None):
    """This is the :math:`(\mu~,~\lambda)` evolutionary algorithm
    """
    assert lambda_ >= mu, "lambda must be greater or equal to mu." 
    assert (cxpb + mutpb) <= 1.0, ("The sum of the crossover and mutation"
        "probabilities must be smaller or equal to 1.0.")
        
    _logger.info("Start of evolution")
    evaluations = 0
    
    # Evaluate the individuals with an invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            evaluations += 1
            ind.fitness.values = toolbox.evaluate(ind)
    
    _logger.debug("Evaluated %i individuals", evaluations)
            
    if halloffame is not None:
        halloffame.update(population)
    
    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        evaluations = 0

        offsprings = []
        nb_offsprings = 0
        while nb_offsprings < lambda_:
        #for i in xrange(lambda_):
            op_choice = random.random()
            if op_choice < cxpb:            # Apply crossover
                p1, p2 = random.sample(population, 2)
                children = toolbox.mate(p1, p2)
                offsprings.extend(children)
                nb_offsprings += len(children)
            elif op_choice < cxpb + mutpb:  # Apply mutation
                p = random.choice(population)
                mutants = toolbox.mutate(p)
                offsprings.extend(mutants)
                nb_offsprings += len(mutants)
            else:                           # Apply reproduction
                offsprings.append(random.choice(population))
                nb_offsprings += 1
        
        # Remove the exedant of offsprings
        if nb_offsprings > lambda_:
            del offsprings[lambda_:]

        # Evaluate the individuals with invalid fitness
        for ind in offsprings:
            if not ind.fitness.valid:
                evaluations += 1
                ind.fitness.values = toolbox.evaluate(ind)

        _logger.debug("Evaluated %i individuals", evaluations)

        if halloffame is not None:
            halloffame.update(offsprings)

        # Select the next generation population
        population[:] = toolbox.select(offsprings, mu)

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values for ind in population]
        fits_t = zip(*fits)             # Transpose fitnesses for analysis

        minimums = map(min, fits_t)
        maximums = map(max, fits_t)
        lenght = len(population)
        sums = map(sum, fits_t)
        sums2 = [sum(map(lambda x: x**2, fit)) for fit in fits_t]
        means = [sum_ / lenght for sum_ in sums]
        std_devs = [abs(sum2 / lenght - mean**2)**0.5 for sum2, mean in zip(sums2, means)]

        _logger.debug("Min %s", ", ".join(map(str, minimums)))
        _logger.debug("Max %s", ", ".join(map(str, maximums)))
        _logger.debug("Avg %s", ", ".join(map(str, means)))
        _logger.debug("Std %s", ", ".join(map(str, std_devs)))

    _logger.info("End of (successful) evolution")
    
def eaSteadyState(toolbox, population, ngen, halloffame=None):
    """The is the steady-state evolutionary algorithm
    """
    _logger.info("Start of evolution")
    
    # Evaluate the individuals with an invalid fitness
    for ind in population:
        if not ind.fitness.valid:
            ind.fitness.extend(toolbox.evaluate(ind))
    
    if halloffame is not None:
        halloffame.update(population)
    
    # Begin the generational process
    for g in range(ngen):
        _logger.info("Evolving generation %i", g)
        
        p1, p2 = toolbox.select(population, 2)
        child = random.choice(toolbox.mate(p1, p2))
        child = random.choice(toolbox.mutate(child))
        
        if not child.fitness.valid:
            child.fitness.extend(toolbox.evaluate(child))
        
        if halloffame is not None:
            halloffame.update(child)
        
        # Select the next generation population
        population[:] = toolbox.select(population + [child], len(population))
        
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values for ind in population]
        fits_t = zip(*fits)             # Transpose fitnesses for analysis
        
        minimums = map(min, fits_t)
        maximums = map(max, fits_t)
        lenght = len(population)
        sums = map(sum, fits_t)
        sums2 = [sum([x*x for x in fit]) for fit in fits_t]
        means = [sum_ / lenght for sum_ in sums]
        std_devs = [abs(sum2 / lenght - mean**2)**0.5 for sum2, mean in zip(sums2, means)]
        
        _logger.debug("Min %s", ", ".join(map(str, minimums)))
        _logger.debug("Max %s", ", ".join(map(str, maximums)))
        _logger.debug("Avg %s", ", ".join(map(str, means)))
        _logger.debug("Std %s", ", ".join(map(str, std_devs)))

    _logger.info("End of (successful) evolution")

