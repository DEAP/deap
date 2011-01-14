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
import time

from eap import base
from eap import creator
from eap import halloffame
from eap import toolbox

from eap import iterations
from eap import statistics

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

tools.register("evaluate", evalOneMax)
tools.register("mate", toolbox.cxTwoPoints)
tools.register("mutate", toolbox.mutFlipBit, indpb=0.05)
tools.register("select", toolbox.selTournament, tournsize=3)

stats_t = statistics.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", statistics.mean)
stats_t.register("Std", statistics.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    random.seed(64)

    demes = [tools.population(), tools.population(), tools.population()]
    hof = halloffame.HallOfFame(1)
    dstats = [tools.clone(stats_t), tools.clone(stats_t), tools.clone(stats_t)]
    pstats = tools.clone(stats_t)

    gmeans = statistics.Stats()
    gmeans.register("Avg", statistics.mean)

    NGEN = 40
    CXPB = 0.5
    MUTPB = 0.2
    gen = 0
    
    for deme, stats in zip(demes, dstats):
        for ind in deme:
            ind.fitness.values = tools.evaluate(ind)
        stats.update(deme)
        hof.update(deme)
    pstats.update(demes[0]+demes[1]+demes[2])
    
    while gen < NGEN and pstats.data['Max'][-1][0] < 100.0:
        print "-- Generation %i --" % gen        
        for idx, deme, stats in zip(xrange(len(demes)), demes, dstats):
            print "  -- Deme %i --" % (idx+1)                
            iterations.eaSimple(tools, deme, cxpb=CXPB, mutpb=MUTPB, stats=stats, halloffame=hof)
            for key, stat in stats.data.items():
                print "    %s %s" % (key, stat[-1][0])
        if gen > 0 and gen % 5 == 0:
            toolbox.migRing(demes, n=5, selection=tools.select)
        pstats.update(demes[0]+demes[1]+demes[2])
        gmeans.update(demes[0]+demes[1]+demes[2])
        print "  -- Population --"  
        for key, stat in pstats.data.items():
            print "    %s %s" % (key, stat[-1][0])        
        gen += 1
    
    return demes, dstats, pstats, hof, gmeans

if __name__ == "__main__":
    main()
