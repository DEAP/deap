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

import random

def eaSimple(toolbox, population, cxpb, mutpb, stats=None, halloffame=None):
    # Select the next generation individuals
    offsprings = toolbox.select(population, n=len(population))
    # Clone the selected individuals
    offsprings = map(toolbox.clone, offsprings)

    # Apply crossover and mutation on the offsprings
    for ind1, ind2 in zip(offsprings[::2], offsprings[1::2]):
        if random.random() < cxpb:
            toolbox.mate(ind1, ind2)
            del ind1.fitness.values
            del ind2.fitness.values

    for ind in offsprings:
        if random.random() < mutpb:
            toolbox.mutate(ind)
            del ind.fitness.values

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(offsprings)
        
    # The population is entirely replaced by the offsprings
    population[:] = offsprings
    
    if stats is not None:
        stats.update(population)
    
    return len(invalid_ind)    

def eaMuPlusLambda(toolbox, population, mu, lambda_, cxpb, mutpb, stats=None, halloffame=None):
    offsprings = []
    nb_offsprings = 0
    while nb_offsprings < lambda_:
    #for i in xrange(lambda_):
        op_choice = random.random()
        if op_choice < cxpb:            # Apply crossover
            ind1, ind2 = random.sample(population, 2)
            ind1 = toolbox.clone(ind1)
            ind2 = toolbox.clone(ind2)
            toolbox.mate(ind1, ind2)
            del ind1.fitness.values
            del ind2.fitness.values
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

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    _logger.debug("Evaluated %i individuals", len(invalid_ind))

    if halloffame is not None:
        halloffame.update(offsprings)

    # Select the next generation population
    population[:] = toolbox.select(population + offsprings, mu)
    
    return len(invalid_ind)
    