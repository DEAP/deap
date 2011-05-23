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
creator.create("Individual", array.array, fitness=creator.FitnessMax)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_bool", random.randint, 0, 1)

# Structure initializers
tools.register("individual", creator.Individual, "b", toolbox.Repeat(tools.attr_bool, 100))
tools.register("population", list, toolbox.Repeat(tools.individual, 300))

def evalOneMax(individual):
    return sum(individual),

tools.register("evaluate", evalOneMax)
tools.register("mate", operators.cxTwoPoints)
tools.register("mutate", operators.mutFlipBit, indpb=0.05)
tools.register("select", operators.selTournament, tournsize=3)
tools.register("migrate", operators.migRing, n=5, selection=operators.selBest,
    replacement=operators.selRandom)

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    random.seed(64)

    demes = [tools.population(), tools.population(), tools.population()]
    hof = operators.HallOfFame(1)
    dstats = [tools.clone(stats_t), tools.clone(stats_t), tools.clone(stats_t)]
    pstats = tools.clone(stats_t)

    gmeans = operators.Stats()
    gmeans.register("Avg", operators.mean)

    NGEN = 40
    CXPB = 0.5
    MUTPB = 0.2
    gen = 1
    
    for deme, stats in zip(demes, dstats):
        for ind in deme:
            ind.fitness.values = tools.evaluate(ind)
        stats.update(deme)
        hof.update(deme)
    pstats.update(demes[0]+demes[1]+demes[2])
    
    while gen <= NGEN and pstats.data['Max'][-1][0] < 100.0:
        print "-- Generation %i --" % gen        
        for idx, deme, stats in zip(xrange(len(demes)), demes, dstats):
            print "  -- Deme %i --" % (idx+1)  
            deme[:] = [tools.clone(ind) for ind in tools.select(deme, len(deme))]
            algorithms.varSimple(tools, deme, cxpb=CXPB, mutpb=MUTPB)
            
            for ind in deme:
                ind.fitness.values = tools.evaluate(ind)
            
            stats.update(deme)
            hof.update(deme)
            for key, stat in stats.data.iteritems():
                print "    %s %s" % (key, stat[-1][0])
        if gen % 5 == 0:
            tools.migrate(demes)
        pstats.update(demes[0]+demes[1]+demes[2])
        gmeans.update(demes[0]+demes[1]+demes[2])
        print "  -- Population --"  
        for key, stat in pstats.data.iteritems():
            print "    %s %s" % (key, stat[-1][0])        
        gen += 1
    
    return demes, dstats, pstats, hof, gmeans

if __name__ == "__main__":
    main()
