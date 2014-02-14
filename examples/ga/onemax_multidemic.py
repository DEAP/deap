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

import numpy

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_bool", random.randint, 0, 1)

# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, 
    toolbox.attr_bool, 100)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evalOneMax(individual):
    return sum(individual),

toolbox.register("evaluate", evalOneMax)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("migrate", tools.migRing, k=5, selection=tools.selBest,
    replacement=random.sample)

def main():
    random.seed(64)

    NBR_DEMES = 3
    MU = 300
    NGEN = 40
    CXPB = 0.5
    MUTPB = 0.2
    MIG_RATE = 5    
    
    demes = [toolbox.population(n=MU) for _ in range(NBR_DEMES)]
    hof = tools.HallOfFame(1)
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "deme", "evals", "std", "min", "avg", "max"
    
    for idx, deme in enumerate(demes):
        for ind in deme:
            ind.fitness.values = toolbox.evaluate(ind)
        logbook.record(gen=0, deme=idx, evals=len(deme), **stats.compile(deme))
        hof.update(deme)
    print(logbook.stream)
    
    gen = 1
    while gen <= NGEN and logbook[-1]["max"] < 100.0:
        for idx, deme in enumerate(demes):
            deme[:] = toolbox.select(deme, len(deme))
            deme[:] = algorithms.varAnd(deme, toolbox, cxpb=CXPB, mutpb=MUTPB)
            
            invalid_ind = [ind for ind in deme if not ind.fitness.valid]
            for ind in invalid_ind:
                ind.fitness.values = toolbox.evaluate(ind)
            
            logbook.record(gen=gen, deme=idx, evals=len(deme), **stats.compile(deme))
            hof.update(deme)
        print(logbook.stream)
            
        if gen % MIG_RATE == 0:
            toolbox.migrate(demes)
        gen += 1
    
    return demes, logbook, hof

if __name__ == "__main__":
    main()
