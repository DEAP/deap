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

import array
import sys
import random
import multiprocessing

sys.path.append("..")

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox

random.seed(64)

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, fitness=creator.FitnessMax)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_bool", random.randint, 0, 1)

# Structure initializers
tools.register("individual", creator.Individual, "b", content_init=tools.attr_bool, size_init=100)
tools.register("population", list, content_init=tools.individual, size_init=300)

def evalOneMax(individual):
    return sum(individual),

tools.register("mate", toolbox.cxTwoPoints)
tools.register("mutate", toolbox.mutFlipBit, indpb=0.05)
tools.register("select", toolbox.selTournament, tournsize=3)

if __name__ == "__main__":

    pop = tools.population()
    CXPB, MUTPB, NGEN = 0.5, 0.2, 40
    
    # Process Pool of 4 workers
    pool = multiprocessing.Pool(processes=4)
    
    fitnesses = pool.map(evalOneMax, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    # Begin the evolution
    for g in range(NGEN):
        print "-- Generation %i --" % g
    
        pop[:] = tools.select(pop, n=len(pop))
    
        # Apply crossover and mutation
        for i in xrange(1, len(pop), 2):
            if random.random() < CXPB:
                pop[i - 1], pop[i] = tools.mate(pop[i - 1], pop[i])
    
        for i in xrange(len(pop)):
            if random.random() < MUTPB:
                pop[i] = tools.mutate(pop[i])
    
        # Evaluate the individuals with an invalid fitness
        invalid_ind = filter(lambda ind: not ind.fitness.valid, pop)
        fitnesses = pool.map(evalOneMax, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        print "  Min %s" % min(fits)
        print "  Max %s" % max(fits)
        lenght = len(pop)
        mean = sum(fits) / lenght
        sum2 = sum(map(lambda x: x**2, fits))
        std_dev = abs(sum2 / lenght - mean**2)**0.5
        print "  Avg %s" % (mean)
        print "  Std %s" % std_dev
    
    print "-- End of (successful) evolution --"
    
    best_ind = toolbox.selBest(pop, 1)[0]
    print "Best individual is %s, %s" % (best_ind, best_ind.fitness.values)
