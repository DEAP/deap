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

from eap import base
from eap import creator
from eap import toolbox

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
creator.create("Population", list)

tools = toolbox.Toolbox()
# Attribute generator
tools.register("attr_bool", random.randint, 0, 1)
# Structure initializers
tools.register("individual", creator.Individual,
    content_init=tools.attr_bool, size_init=100)
tools.register("population", creator.Population,
    content_init=tools.individual, size_init=300)

def evalOneMax(individual):
    return sum(individual),

# Operator registering
tools.register("evaluate", evalOneMax)
tools.register("mate", toolbox.cxTwoPoints)
tools.register("mutate", toolbox.mutFlipBit, indpb=0.05)
tools.register("select", toolbox.selTournament, tournsize=3)

def main():
    random.seed(64)
    
    pop = tools.population()
    CXPB, MUTPB, NGEN = 0.5, 0.2, 40
    
    print "Start of evolution"
    
    # Evaluate the entire population
    fitnesses = map(tools.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    
    print "  Evaluated %i individuals" % len(pop)
    
    # Begin the evolution
    for g in range(NGEN):
        print "-- Generation %i --" % g
        
        # Select the next generation individuals
        offsprings = tools.select(pop, n=len(pop))
        # Clone the selected individuals
        offsprings = map(tools.clone, offsprings)
    
        # Apply crossover and mutation on the offsprings
        for child1, child2 in zip(offsprings[::2], offsprings[1::2]):
            if random.random() < CXPB:
                tools.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offsprings:
            if random.random() < MUTPB:
                tools.mutate(mutant)
                del mutant.fitness.values
    
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
        fitnesses = map(tools.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        print "  Evaluated %i individuals" % len(invalid_ind)
        
        # The population is entirely replaced by the offsprings
        pop[:] = offsprings
        
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std_dev = abs(sum2 / length - mean**2)**0.5
        
        print "  Min %s" % min(fits)
        print "  Max %s" % max(fits)
        print "  Avg %s" % mean
        print "  Std %s" % std_dev
    
    print "-- End of (successful) evolution --"
    
    best_ind = toolbox.selBest(pop, 1)[0]
    print "Best individual is %s, %s" % (best_ind, best_ind.fitness.values)

if __name__ == "__main__":
    main()
