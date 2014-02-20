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

import sys
import random
import logging
import time

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

import SNC as snc
# ...
import sortingnetwork as sn

INPUTS = 11

def evalEvoSN(individual, dimension):
    fit,depth,length= snc.evalNetwork(dimension, individual)
    return fit, length, depth

def genWire(dimension):
    return (random.randrange(dimension), random.randrange(dimension))
    
def genNetwork(dimension, min_size, max_size):
    size = random.randint(min_size, max_size)
    return [genWire(dimension) for i in xrange(size)]
    
def mutWire(individual, dimension, indpb):
    for index, elem in enumerate(individual):
        if random.random() < indpb:
            individual[index] = genWire(dimension)      

def mutAddWire(individual, dimension):
    index = random.randint(0, len(individual))
    individual.insert(index, genWire(dimension))

def mutDelWire(individual):
    index = random.randrange(len(individual))
    del individual[index]

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Gene initializer
toolbox.register("network", genNetwork, dimension=INPUTS, min_size=9, max_size=12)

# Structure initializers
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.network)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
# ...
toolbox.register("evaluate", evalEvoSN, dimension=INPUTS)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", mutWire, dimension=INPUTS, indpb=0.05)
toolbox.register("addwire", mutAddWire, dimension=INPUTS)
toolbox.register("delwire", mutDelWire)
toolbox.register("select", tools.selNSGA2)

def main():
    random.seed(64)

    population = toolbox.population(n=500)
    hof = tools.ParetoFront()
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", tools.mean)
    stats.register("Std", tools.std)
    stats.register("Min", min)
    stats.register("Max", max)

    CXPB, MUTPB, ADDPB, DELPB, NGEN = 0.5, 0.2, 0.01, 0.01, 10
    
    # Evaluate every individuals
    fitnesses = toolbox.map(toolbox.evaluate, population)
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit
    
    hof.update(population)
    stats.update(population)
    
    # Begin the evolution
    for g in xrange(NGEN):
        t1 = time.time()
        print "-- Generation %i --" % g
        offspring = [toolbox.clone(ind) for ind in population]
        t2 = time.time()
        # Apply crossover and mutation
        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values
        t3 = time.time()
        # Note here that we have a different sheme of mutation than in the
        # original algorithm, we use 3 different mutations subsequently.
        for ind in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(ind)
                del ind.fitness.values
            if random.random() < ADDPB:
                toolbox.addwire(ind)
                del ind.fitness.values
            if random.random() < DELPB:
                toolbox.delwire(ind)
                del ind.fitness.values
        t4 = time.time()
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        print "  Evaluated %i individuals" % len(invalid_ind)
        t5 = time.time()
        population = toolbox.select(population+offspring, len(offspring))
        t6 = time.time()
        #hof.update(population)
        stats.update(population)
        t7 = time.time()
        print stats
        
        print("Times :")
        print("Clone : " + str(t2-t1) + " (" + str((t2-t1)/(t7-t1)) +"%)")
        print("Cx : " + str(t3-t2) + " (" + str((t3-t2)/(t7-t1)) +"%)")
        print("Mut : " + str(t4-t3) + " (" + str((t4-t3)/(t7-t1)) +"%)")
        print("Eval : " + str(t5-t4) + " (" + str((t5-t4)/(t7-t1)) +"%)")
        print("Select : " + str(t6-t5) + " (" + str((t6-t5)/(t7-t1)) +"%)")
        print("HOF + stats : " + str(t7-t6) + " (" + str((t7-t6)/(t7-t1)) +"%)")
        print("TOTAL : " + str(t7-t1))
        

    best_network = sn.SortingNetwork(INPUTS, hof[0])
    print best_network
    print best_network.draw()
    print "%i errors, length %i, depth %i" % hof[0].fitness.values
    
    return population, stats, hof

if __name__ == "__main__":
    main()
