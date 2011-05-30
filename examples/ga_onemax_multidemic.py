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

import array
import random

from deap import algorithms
from deap import base
from deap import creator
from deap import operators
from deap import toolbox

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMax)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_bool", random.randint, 0, 1)

# Structure initializers
tools.register("individual", toolbox.fillRepeat, creator.Individual, 
    tools.attr_bool, 100)
tools.register("population", toolbox.fillRepeat, list, tools.individual)

def evalOneMax(individual):
    return sum(individual),

tools.register("evaluate", evalOneMax)
tools.register("mate", operators.cxTwoPoints)
tools.register("mutate", operators.mutFlipBit, indpb=0.05)
tools.register("select", operators.selTournament, tournsize=3)
tools.register("migrate", operators.migRing, n=5, selection=operators.selBest,
    replacement=operators.selRandom)

def main():
    random.seed(64)

    NBR_DEMES = 3
    MU = 300
    NGEN = 40
    CXPB = 0.5
    MUTPB = 0.2
    MIG_RATE = 5    
    
    demes = [tools.population(n=MU) for _ in xrange(NBR_DEMES)]
    hof = operators.HallOfFame(1)
    stats = operators.Statistics(lambda ind: ind.fitness.values, 4)
    stats.register("Avg", operators.mean)
    stats.register("Std", operators.std_dev)
    stats.register("Min", min)
    stats.register("Max", max)
    
    stats0 = operators.Statistics(lambda ind: ind[0], 4)
    stats0.register("Avg", operators.mean)
    stats0.register("Std", operators.std_dev)
    stats0.register("Min", min)
    stats0.register("Max", max)    
    
    for idx, deme in enumerate(demes):
        for ind in deme:
            ind.fitness.values = tools.evaluate(ind)
        stats.update(deme, idx)
        hof.update(deme)
    stats.update(demes[0]+demes[1]+demes[2], 3)
    
    gen = 1
    while gen <= NGEN and stats.Max(3)[0] < 100.0:
        print "-- Generation %i --" % gen        
        for idx, deme in enumerate(demes):
            print "-- Deme %i --" % (idx+1)  
            deme[:] = [tools.clone(ind) for ind in tools.select(deme, len(deme))]
            algorithms.varSimple(tools, deme, cxpb=CXPB, mutpb=MUTPB)
            
            for ind in deme:
                ind.fitness.values = tools.evaluate(ind)
            
            stats.update(deme, idx)
            stats0.update(deme, idx)
            hof.update(deme)
            print stats[idx]
        if gen % MIG_RATE == 0:
            tools.migrate(demes)
        stats.update(demes[0]+demes[1]+demes[2], 3)
        stats0.update(demes[0]+demes[1]+demes[2], 3)
        print "-- Population --"
        print stats[3]
        print "--- Stats ind[0] ----"
        print stats0
        gen += 1
    
    return demes, stats, hof

if __name__ == "__main__":
    main()
