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

import random
import sys

import numpy

from deap import base
from deap import creator
from deap import tools

# GP example "symbreg.py" already defines some useful structures
sys.path.append("..")
import gp.symbreg as symbreg

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("IndGA", list, fitness=creator.FitnessMax)

toolbox_ga = base.Toolbox()

toolbox_ga.register("float", random.uniform, -1, 1)
toolbox_ga.register("individual", tools.initRepeat, creator.IndGA, toolbox_ga.float, 10)
toolbox_ga.register("population", tools.initRepeat, list, toolbox_ga.individual)

toolbox_ga.register("select", tools.selTournament, tournsize=3)
toolbox_ga.register("mate", tools.cxTwoPoint)
toolbox_ga.register("mutate", tools.mutGaussian, mu=0, sigma=0.01, indpb=0.05)

toolbox_gp = symbreg.toolbox

def main():
    pop_ga = toolbox_ga.population(n=200)
    pop_gp = toolbox_gp.population(n=200)
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "type", "evals", "std", "min", "avg", "max"
    
    best_ga = tools.selRandom(pop_ga, 1)[0]
    best_gp = tools.selRandom(pop_gp, 1)[0]
    
    for ind in pop_gp:
        ind.fitness.values = toolbox_gp.evaluate(ind, points=best_ga)  
    
    for ind in pop_ga:
        ind.fitness.values = toolbox_gp.evaluate(best_gp, points=ind)
    
    record = stats.compile(pop_ga)
    logbook.record(gen=0, type='ga', evals=len(pop_ga), **record)
    
    record = stats.compile(pop_gp)
    logbook.record(gen=0, type='gp', evals=len(pop_gp), **record)
    
    print(logbook.stream)
    
    CXPB, MUTPB, NGEN = 0.5, 0.2, 50
    
    # Begin the evolution
    for g in range(1, NGEN):
        # Select and clone the offspring
        off_ga = toolbox_ga.select(pop_ga, len(pop_ga))
        off_gp = toolbox_gp.select(pop_gp, len(pop_gp))
        off_ga = [toolbox_ga.clone(ind) for ind in off_ga]        
        off_gp = [toolbox_gp.clone(ind) for ind in off_gp]
    
    
        # Apply crossover and mutation
        for ind1, ind2 in zip(off_ga[::2], off_ga[1::2]):
            if random.random() < CXPB:
                toolbox_ga.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values
    
        for ind1, ind2 in zip(off_gp[::2], off_gp[1::2]):
            if random.random() < CXPB:
                toolbox_gp.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values
    
        for ind in off_ga:
            if random.random() < MUTPB:
                toolbox_ga.mutate(ind)
                del ind.fitness.values
    
        for ind in off_gp:
            if random.random() < MUTPB:
                toolbox_gp.mutate(ind)
                del ind.fitness.values
    
        # Evaluate the individuals with an invalid fitness
        for ind in off_ga:
            ind.fitness.values = toolbox_gp.evaluate(best_gp, points=ind)
        
        for ind in off_gp:
            ind.fitness.values = toolbox_gp.evaluate(ind, points=best_ga)
                
        # Replace the old population by the offspring
        pop_ga = off_ga
        pop_gp = off_gp
        
        record = stats.compile(pop_ga)
        logbook.record(gen=g, type='ga', evals=len(pop_ga), **record)
        
        record = stats.compile(pop_gp)
        logbook.record(gen=g, type='gp', evals=len(pop_gp), **record)
        print(logbook.stream)
        
        
        best_ga = tools.selBest(pop_ga, 1)[0]
        best_gp = tools.selBest(pop_gp, 1)[0]
    

    print("Best individual GA is %s, %s" % (best_ga, best_ga.fitness.values))
    print("Best individual GP is %s, %s" % (best_gp, best_gp.fitness.values))

    return pop_ga, pop_gp, best_ga, best_gp, logbook

if __name__ == "__main__":
    main()
