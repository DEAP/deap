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

import random
import tools

def varSimple(toolbox, population, cxpb, mutpb):
    """Part of the :func:`~deap.algorithmes.eaSimple` algorithm applying only
    the variation part (crossover followed by mutation). The modified 
    individuals have their fitness invalidated. The individuals are not cloned
    so there can be twice a reference to the same individual.
    
    This function expects :meth:`toolbox.mate` and :meth:`toolbox.mutate`
    aliases to be registered in the toolbox.
    """
    # Apply crossover and mutation on the offspring
    for ind1, ind2 in zip(population[::2], population[1::2]):
        if random.random() < cxpb:
            toolbox.mate(ind1, ind2)
            del ind1.fitness.values, ind2.fitness.values

    for ind in population:
        if random.random() < mutpb:
            toolbox.mutate(ind)
            del ind.fitness.values
    
    return population

def varAnd(toolbox, population, cxpb, mutpb):
    """Part of an evolutionary algorithm applying only the variation part
    (crossover **and** mutation). The modified individuals have their
    fitness invalidated. The individuals are cloned so returned population is
    independent of the input population.
    
    The variator goes as follow. First, the parental population
    :math:`P_\mathrm{p}` is duplicated using the :meth:`toolbox.clone` method
    and the result is put into the offspring population :math:`P_\mathrm{o}`.
    A first loop over :math:`P_\mathrm{o}` is executed to mate consecutive
    individuals. According to the crossover probability *cxpb*, the
    individuals :math:`\mathbf{x}_i` and :math:`\mathbf{x}_{i+1}` are mated
    using the :meth:`toolbox.mate` method. The resulting children
    :math:`\mathbf{y}_i` and :math:`\mathbf{y}_{i+1}` replace their respective
    parents in :math:`P_\mathrm{o}`. A second loop over the resulting
    :math:`P_\mathrm{o}` is executed to mutate every individual with a
    probability *mutpb*. When an individual is mutated it replaces its not
    mutated version in :math:`P_\mathrm{o}`. The resulting
    :math:`P_\mathrm{o}` is returned.
    
    This variation is named *And* beceause of its propention to apply both
    crossover and mutation on the individuals. Note that both operators are
    not applied systematicaly, the resulting individuals can be generated from
    crossover only, mutation only, crossover and mutation, and reproduction
    according to the given probabilities. Both probabilities should be in
    :math:`[0, 1]`.
    """
    offspring = [toolbox.clone(ind) for ind in population]
    
    # Apply crossover and mutation on the offspring
    for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
        if random.random() < cxpb:
            toolbox.mate(ind1, ind2)
            del ind1.fitness.values, ind2.fitness.values
    
    for ind in offspring:
        if random.random() < mutpb:
            toolbox.mutate(ind)
            del ind.fitness.values
    
    return offspring

def eaSimple(toolbox, population, cxpb, mutpb, ngen, stats=None,
             halloffame=None, logger=None):
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
            offspring = select(population)
            offspring = mate(offspring)
            offspring = mutate(offspring)
            evaluate(offspring)
            population = offspring
    
    This function expects :meth:`toolbox.mate`, :meth:`toolbox.mutate`,
    :meth:`toolbox.select` and :meth:`toolbox.evaluate` aliases to be
    registered in the toolbox.
    """
    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)
    if stats is not None:
        stats.update(population)
    if logger is not None:
        logger.printHeader()
        if stats is not None:
            logger.logStatistics(stats, len(population), 0)
        else:
            logger.logGeneration(len(invalid_ind), 0)

    # Begin the generational process
    for gen in range(1, ngen+1):
        # Select and clone the next generation individuals
        offsprings = toolbox.select(population, len(population))
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
            
        # Replace the current population by the offsprings
        population[:] = offsprings
        
        # Update the statistics with the new population
        if stats is not None:
            stats.update(population)

        if logger is not None:
            if stats is not None:
                logger.logStatistics(stats, len(invalid_ind), gen)
            else:
                logger.logGeneration(len(invalid_ind), gen)

    return population

def varOr(toolbox, population, lambda_, cxpb, mutpb):
    """Part of an evolutionary algorithm applying only the variation part
    (crossover, mutation **or** reproduction). The modified individuals have
    their fitness invalidated. The individuals are cloned so returned
    population is independent of the input population.
    
    The variator goes as follow. On each of the *lambda_* iteration, it
    selects one of the three operations; crossover, mutation or reproduction.
    In the case of a crossover, two individuals are selected at random from
    the parental population :math:`P_\mathrm{p}`, those individuals are cloned
    using the :meth:`toolbox.clone` method and then mated using the
    :meth:`toolbox.mate` method. Only the first child is appended to the
    offspring population :math:`P_\mathrm{o}`, the second child is discarded.
    In the case of a mutation, one individual is selected at random from
    :math:`P_\mathrm{p}`, it is cloned and then mutated using using the
    :meth:`toolbox.mutate` method. The resulting mutant is appended to
    :math:`P_\mathrm{o}`. In the case of a reproduction, one individual is
    selected at random from :math:`P_\mathrm{p}`, cloned and appended to
    :math:`P_\mathrm{o}`.
    
    This variation is named *Or* beceause an offspring will never result from
    both operations crossover and mutation. The sum of both probabilities
    shall be in :math:`[0, 1]`, the reproduction probability is
    1 - *cxpb* - *mutpb*.
    """
    assert (cxpb + mutpb) <= 1.0, ("The sum of the crossover and mutation "
        "probabilities must be smaller or equal to 1.0.")
        
    offsprings = []
    for _ in xrange(lambda_):
        op_choice = random.random()
        if op_choice < cxpb:            # Apply crossover
            ind1, ind2 = [toolbox.clone(ind) for ind in random.sample(population, 2)]
            toolbox.mate(ind1, ind2)
            del ind1.fitness.values
            offsprings.append(ind1)
        elif op_choice < cxpb + mutpb:  # Apply mutation
            ind = toolbox.clone(random.choice(population))
            toolbox.mutate(ind)
            del ind.fitness.values
            offsprings.append(ind)
        else:                           # Apply reproduction
            offsprings.append(random.choice(population))
    
    return offsprings

def varLambda(toolbox, population, lambda_, cxpb, mutpb):
    """Part of the :func:`~deap.algorithms.eaMuPlusLambda` and
    :func:`~deap.algorithms.eaMuCommaLambda` algorithms that produce the 
    lambda new individuals. The modified individuals have their fitness 
    invalidated. The individuals are not cloned so there can be twice a
    reference to the same individual.
    
    This function expects :meth:`toolbox.mate` and :meth:`toolbox.mutate`
    aliases to be registered in the toolbox.
    """
    assert (cxpb + mutpb) <= 1.0, ("The sum of the crossover and mutation "
        "probabilities must be smaller or equal to 1.0.")
        
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

def eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen,
                   stats=None, halloffame=None, logger=None):
    """This is the :math:`(\mu + \lambda)` evolutionary algorithm. First, 
    the individuals having an invalid fitness are evaluated. Then, the
    evolutionary loop begins by producing *lambda* offspring from the
    population, the offspring are generated by a crossover, a mutation or a
    reproduction proportionally to the probabilities *cxpb*, *mutpb* and
    1 - (cxpb + mutpb). The offspring are then evaluated and the next
    generation population is selected from both the offspring **and** the
    population. Briefly, the operators are applied as following ::
    
        evaluate(population)
        for i in range(ngen):
            offspring = generate_offspring(population)
            evaluate(offspring)
            population = select(population + offspring)
    
    This function expects :meth:`toolbox.mate`, :meth:`toolbox.mutate`,
    :meth:`toolbox.select` and :meth:`toolbox.evaluate` aliases to be
    registered in the toolbox.
    
    .. note::
       Both produced individuals from a crossover are put in the offspring
       pool. 
    
    """
    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)
    if stats is not None:
        stats.update(population)
    if logger is not None:
        logger.printHeader()
        if stats is not None:
            logger.logStatistics(stats, len(invalid_ind), 0)
        else:
            logger.logGeneration(len(invalid_ind), gen)

    # Begin the generational process
    for gen in range(1, ngen+1):
        # Variate the population
        offsprings = varLambda(toolbox, population, lambda_, cxpb, mutpb)
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offsprings)

        # Select the next generation population
        population[:] = toolbox.select(population + offsprings, mu)

        # Update the statistics with the new population
        if stats is not None:
            stats.update(population)
        if logger is not None:
            if stats is not None:
                logger.logStatistics(stats, len(invalid_ind), gen)
            else:
                logger.logGeneration(len(invalid_ind), gen)

    return population
    
def eaMuCommaLambda(toolbox, population, mu, lambda_, cxpb, mutpb, ngen,
                    stats=None, halloffame=None, logger=None):
    """This is the :math:`(\mu~,~\lambda)` evolutionary algorithm. First, 
    the individuals having an invalid fitness are evaluated. Then, the
    evolutionary loop begins by producing *lambda* offspring from the
    population, the offspring are generated by a crossover, a mutation or a
    reproduction proportionally to the probabilities *cxpb*, *mutpb* and
    1 - (cxpb + mutpb). The offspring are then evaluated and the next
    generation population is selected **only** from the offspring. Briefly,
    the operators are applied as following ::
    
        evaluate(population)
        for i in range(ngen):
            offspring = generate_offspring(population)
            evaluate(offspring)
            population = select(offspring)
    
    This function expects :meth:`toolbox.mate`, :meth:`toolbox.mutate`,
    :meth:`toolbox.select` and :meth:`toolbox.evaluate` aliases to be
    registered in the toolbox.
    
    .. note::
       Both produced individuals from the crossover are put in the offspring
       pool.
    """
    assert lambda_ >= mu, "lambda must be greater or equal to mu."

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)
    if stats is not None:
        stats.update(population)
    if logger is not None:
        logger.printHeader()
        if stats is not None:
            logger.logStatistics(stats, len(population), 0)
        else:
            logger.logGeneration(len(invalid_ind), 0)


    # Begin the generational process
    for gen in range(1, ngen+1):
        # Variate the population
        offsprings = varLambda(toolbox, population, lambda_, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offsprings)

        # Select the next generation population
        population[:] = toolbox.select(offsprings, mu)

        # Update the statistics with the new population
        if stats is not None:
            stats.update(population)
        if logger is not None:
            if stats is not None:
                logger.logStatistics(stats, len(invalid_ind), gen)
            else:
                logger.logGeneration(len(invalid_ind), gen)

    return population

def varSteadyState(toolbox, population):
    """Part of the :func:`~deap.algorithms.eaSteadyState` algorithm 
    that produce the new individual by crossover of two randomly selected 
    parents and mutation on one randomly selected child. The modified 
    individual has its fitness invalidated. The individuals are not cloned so
    there can be twice a reference to the same individual.
    
    This function expects :meth:`toolbox.mate`, :meth:`toolbox.mutate` and
    :meth:`toolbox.select` aliases to be
    registered in the toolbox.
    """
    # Select two individuals for crossover
    p1, p2 = random.sample(population, 2)
    p1 = toolbox.clone(p1)
    p2 = toolbox.clone(p2)
    toolbox.mate(p1, p2)
    
    # Randomly choose amongst the offsprings the returned child and mutate it
    child = random.choice((p1, p2))
    toolbox.mutate(child)
    
    return child,

def eaSteadyState(toolbox, population, ngen, stats=None, halloffame=None,
                  logger=None):
    """The steady-state evolutionary algorithm. Every generation, a single new
    individual is produced and put in the population producing a population of
    size :math:`lambda+1`, then :math:`lambda` individuals are kept according
    to the selection operator present in the toolbox.
    
    This function expects :meth:`toolbox.mate`, :meth:`toolbox.mutate`,
    :meth:`toolbox.select` and :meth:`toolbox.evaluate` aliases to be
    registered in the toolbox.
    """
    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit
    
    if halloffame is not None:
        halloffame.update(population)
    if stats is not None:
        stats.update(population)

    if logger is not None:
        if stats is not None:
            logger.logStatistics(stats, len(population), 0)
        else:
            logger.logGeneration(len(invalid_ind), 0)

    # Begin the generational process
    for gen in range(ngen):
        # Variate the population
        child, = varSteadyState(toolbox, population)

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
        if logger is not None:
            if stats is not None:
                logger.logStatistics(stats, len(invalid_ind), gen)
            else:
                logger.logGeneration(len(invalid_ind), gen)


    return population
