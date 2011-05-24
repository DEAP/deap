#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

"""The :mod:`algorithms` module is intended to contain some specific algorithms
in order to execute very common evolutionary algorithms. The method used here
are more for convenience than reference as the implementation of every 
evolutionary algorithm may vary infinitely. Most of the algorithms in this module
use operators registered in the toolbox. Generaly, the keyword used are
:meth:`mate` for crossover, :meth:`mutate` for mutation, :meth:`~deap.select`
for selection and :meth:`evaluate` for evaluation.

You are encouraged to write your own algorithms in order to make them do what
you really want them to do.
"""

import logging
import random

_logger = logging.getLogger("deap.algorithms")

def varSimple(toolbox, population, cxpb, mutpb):
    """Part of the :func:`~deap.algorithmes.eaSimple` algorithm applying only
    the variation part (crossover followed by mutation). The modified 
    individuals have their fitness invalidated.
    
    This function is not responsible for duplicating the individuals.
    """
    # Apply crossover and mutation on the offsprings
    for ind1, ind2 in zip(population[::2], population[1::2]):
        if random.random() < cxpb:
            toolbox.mate(ind1, ind2)
            del ind1.fitness.values, ind2.fitness.values

    for ind in population:
        if random.random() < mutpb:
            toolbox.mutate(ind)
            del ind.fitness.values
    
    return population

def eaSimple(toolbox, population, cxpb, mutpb, ngen, stats=None, halloffame=None):
    """This algorithm reproduce the simplest evolutionary algorithm as
    presented in chapter 7 of Back, Fogel and Michalewicz,
    "Evolutionary Computation 1 : Basic Algorithms and Operators", 2000.
    It uses :math:`\lambda = \kappa = \mu` and goes as follow.
    It first initializes the population (:math:`P(0)`) by evaluating
    every individual presenting an invalid fitness. Then, it enters the
    evolution loop that begins by the selection of the :math:`P(g+1)`
    population. Then the crossover operator is applied on a proportion of
    :math:`P(g+1)` according to the *cxpb* probability, the resulting and the
    untouched individuals are placed in :math:`P'(g+1)`. Thereafter, a
    proportion of :math:`P'(g+1)`, determined by *mutpb*, is 
    mutated and placed in :math:`P''(g+1)`, the untouched individuals are
    transferred :math:`P''(g+1)`. Finally, those new individuals are evaluated
    and the evolution loop continues until *ngen* generations are completed.
    Briefly, the operators are applied in the following order ::
    
        evaluate(population)
        for i in range(ngen):
            offsprings = select(population)
            offsprings = mate(offsprings)
            offsprings = mutate(offsprings)
            evaluate(offsprings)
            population = offsprings
    
    """
    _logger.info("Start of evolution")

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)
    if stats is not None:
        stats.update(population)

    # Begin the generational process
    for gen in range(ngen):
        _logger.info("Evolving generation %i", gen)
        # Select and clone the next generation individuals
        offsprings = toolbox.select(population, n=len(population))
        offsprings = map(toolbox.clone, offsprings)
        
        # Variate the pool of individuals
        offsprings = varSimple(toolbox, offsprings, cxpb, mutpb)
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offsprings)
            
        _logger.debug("Evaluated %i individuals", len(invalid_ind))  
        
        # Replace the current population by the offsprings
        population[:] = offsprings
        
        # Update the statistics with the new population
        if stats is not None:
            stats.update(population)
        
        # Log statistics on the current generation
        if stats is not None:
            for key, stat in stats.data.iteritems():
                _logger.debug("%s %s" % (key, ", ".join(map(str, stat[-1]))))

    _logger.info("End of (successful) evolution")
    return population

def varMuLambda(toolbox, population, lambda_, cxpb, mutpb):
    """Part of the :func:`~deap.algorithms.eaMuPlusLambda` and
    :func:`~deap.algorithms.eaMuCommaLambda` algorithms that produce the 
    lambda new individuals. The modified individuals have their fitness 
    invalidated.
    
    This function is not responsible for duplicating the individuals.
    """
    offsprings = []
    nb_offsprings = 0
    while nb_offsprings < lambda_:
        op_choice = random.random()
        if op_choice < cxpb:            # Apply crossover
            ind1, ind2 = random.sample(population, 2)
            ind1 = toolbox.clone(ind1)
            ind2 = toolbox.clone(ind2)
            toolbox.mate(ind1, ind2)
            del ind1.fitness.values, ind2.fitness.values
            offsprings.append(ind1)
            offsprings.append(ind2)
            nb_offsprings += 2
        elif op_choice < cxpb + mutpb:  # Apply mutation
            ind = random.choice(population) # select
            ind = toolbox.clone(ind) # clone
            toolbox.mutate(ind)
            del ind.fitness.values
            offsprings.append(ind)
            nb_offsprings += 1
        else:                           # Apply reproduction
            offsprings.append(random.choice(population))
            nb_offsprings += 1
    
    # Remove the exedant of offsprings
    if nb_offsprings > lambda_:
        del offsprings[lambda_:]
    
    return offsprings

def eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen, stats=None, halloffame=None):
    """This is the :math:`(\mu + \lambda)` evolutionary algorithm. First, 
    the individuals having an invalid fitness are evaluated. Then, the
    evolutionary loop begins by producing *lambda* offsprings from the
    population, the offsprings are generated by a crossover, a mutation or a
    reproduction proportionally to the probabilities *cxpb*, *mutpb* and
    1 - (cxpb + mutpb). The offsprings are then evaluated and the next
    generation population is selected from both the offsprings **and** the
    population. Briefly, the operators are applied as following ::
    
        evaluate(population)
        for i in range(ngen):
            offsprings = generate_offsprings(population)
            evaluate(offsprings)
            population = select(population + offsprings)
    
    .. note::
       Both produced individuals from a crossover are put in the offspring
       pool. 
    
    """
    assert (cxpb + mutpb) <= 1.0, ("The sum of the crossover and mutation"
        "probabilities must be smaller or equal to 1.0.")
    
    _logger.info("Start of evolution")

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    _logger.debug("Evaluated %i individuals", len(invalid_ind))

    if halloffame is not None:
        halloffame.update(population)
    if stats is not None:
        stats.update(population)

    # Begin the generational process
    for gen in range(ngen):
        _logger.info("Evolving generation %i", gen)
        
        # Variate the population
        offsprings = varMuLambda(toolbox, population, lambda_, cxpb, mutpb)
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        _logger.debug("Evaluated %i individuals", len(invalid_ind))
        
        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offsprings)

        # Select the next generation population
        population[:] = toolbox.select(population + offsprings, mu)

        # Update the statistics with the new population
        if stats is not None:
            stats.update(population)
        
        # Log statistics on the current generation
        if stats is not None:
            for key, stat in stats.data.iteritems():
                _logger.debug("%s %s" % (key, ", ".join(map(str, stat[-1]))))

    _logger.info("End of (successful) evolution")
    return population
    
def eaMuCommaLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen, stats=None, halloffame=None):
    """This is the :math:`(\mu~,~\lambda)` evolutionary algorithm. First, 
    the individuals having an invalid fitness are evaluated. Then, the
    evolutionary loop begins by producing *lambda* offsprings from the
    population, the offsprings are generated by a crossover, a mutation or a
    reproduction proportionally to the probabilities *cxpb*, *mutpb* and
    1 - (cxpb + mutpb). The offsprings are then evaluated and the next
    generation population is selected **only** from the offsprings. Briefly,
    the operators are applied as following ::
    
        evaluate(population)
        for i in range(ngen):
            offsprings = generate_offsprings(population)
            evaluate(offsprings)
            population = select(offsprings)
    
    .. note::
       Both produced individuals from the crossover are put in the offspring
       pool.
    """
    assert lambda_ >= mu, "lambda must be greater or equal to mu." 
    assert (cxpb + mutpb) <= 1.0, ("The sum of the crossover and mutation"
        "probabilities must be smaller or equal to 1.0.")
        
    _logger.info("Start of evolution")

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    _logger.debug("Evaluated %i individuals", len(invalid_ind))

    if halloffame is not None:
        halloffame.update(population)
    if stats is not None:
        stats.update(population)

    # Begin the generational process
    for gen in range(ngen):
        _logger.info("Evolving generation %i", gen)
        
        # Variate the population
        offsprings = varMuLambda(toolbox, population, lambda_, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        _logger.debug("Evaluated %i individuals", len(invalid_ind))

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offsprings)

        # Select the next generation population
        population[:] = toolbox.select(offsprings, mu)

        # Update the statistics with the new population
        if stats is not None:
            stats.update(population)

        # Log statistics on the current generation
        if stats is not None:
            for key, stat in stats.data.iteritems():
                _logger.debug("%s %s" % (key, ", ".join(map(str, stat[-1]))))

    _logger.info("End of (successful) evolution")
    return population

def varSteadyState(toolbox, population):
    """Part of the :func:`~deap.algorithms.eaSteadyState` algorithm 
    that produce the new individual by crossover of two randomly selected 
    parents and mutation on one randomly selected child. The modified 
    individual has its fitness invalidated.
    
    This function is not responsible for duplicating the individuals.
    """
    # Select two individuals for crossover
    p1, p2 = toolbox.select(population, 2)
    p1 = toolbox.clone(p1)
    p2 = toolbox.clone(p2)
    toolbox.mate(p1, p2)
    
    # Randomly choose amongst the offsprings the returned child and mutate it
    child = random.choice((p1, p2))
    toolbox.mutate(child)
    
    return child

def eaSteadyState(toolbox, population, ngen, stats=None, halloffame=None):
    """The steady-state evolutionary algorithm. Every generation, a single new
    individual is produced and put in the population producing a population of
    size :math:`lambda+1`, then :math:`lambda` individuals are kept according
    to the selection operator present in the toolbox.
    """
    _logger.info("Start of evolution")
    
    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit
    
    if halloffame is not None:
        halloffame.update(population)
    
    # Begin the generational process
    for gen in range(ngen):
        _logger.info("Evolving generation %i", gen)
        
        # Variate the population
        child = varSteadyState(toolbox, population)
        
        # Evaluate the produced child
        child.fitness.values = toolbox.evaluate(child)
        
        # Update the hall of fame
        if halloffame is not None:
            halloffame.update((child,))
        
        # Select the next generation population
        population[:] = toolbox.select(population + [child], len(population))
        
        # Update the statistics with the new population
        if stats is not None:
            stats.update(population)

        # Log statistics on the current generation
        if stats is not None:
            for key, stat in stats.data.iteritems():
                _logger.debug("%s %s" % (key, ", ".join(map(str, stat[-1]))))

    _logger.info("End of (successful) evolution")
    return population
