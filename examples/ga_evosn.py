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

import sys
import random
import logging
import copy

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from eap import algorithms
from eap import base
from eap import creator
from eap import halloffame
from eap import toolbox

import sortingnetwork as sn

INPUTS = 6

def evalEvoSN(individual, dimension):
    network = sn.SortingNetwork(dimension, individual)
    return network.assess(), network.length, network.depth

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

tools = toolbox.Toolbox()

# Gene initializer
tools.register("network", genNetwork, dimension=INPUTS, min_size=9, max_size=12)

# Structure initializers
tools.register("individual", creator.Individual, content_init=tools.network)
tools.register("population", list, content_init=tools.individual, size_init=300)

tools.register("evaluate", evalEvoSN, dimension=INPUTS)
tools.register("mate", toolbox.cxTwoPoints)
tools.register("mutate", mutWire, dimension=INPUTS, indpb=0.05)
tools.register("addwire", mutAddWire, dimension=INPUTS)
tools.register("delwire", mutDelWire)

tools.register("select", toolbox.nsga2)

def main():
    #random.seed(64)

    population = tools.population()
    hof = halloffame.ParetoFront()

    CXPB, MUTPB, ADDPB, DELPB, NGEN = 0.5, 0.2, 0.01, 0.01, 40
    
    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = tools.map(tools.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit
    
    hof.update(population)
    
    # Begin the evolution
    for g in xrange(NGEN):
        print "-- Generation %i --" % g
        offsprings = [tools.clone(ind) for ind in population]
    
        # Apply crossover and mutation
        for ind1, ind2 in zip(offsprings[::2], offsprings[1::2]):
            if random.random() < CXPB:
                tools.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values
        
        # Note here that we have a different sheme of mutation than in the
        # original algorithm, we use 3 different mutations subsequently.
        for ind in offsprings:
            if random.random() < MUTPB:
                tools.mutate(ind)
                del ind.fitness.values
            if random.random() < ADDPB:
                tools.addwire(ind)
                del ind.fitness.values
            if random.random() < DELPB:
                tools.delwire(ind)
                del ind.fitness.values
                
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
        fitnesses = tools.map(tools.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        print "  Evaluated %i individuals" % len(invalid_ind)
        
        population = tools.select(population+offsprings, n=len(offsprings))
        hof.update(population)
        fits = [ind.fitness.values for ind in population]
        
        # Gather all the fitnesses in one list and print the stats
        fits_t = zip(*fits)             # Transpose fitnesses for analysis

        minimums = map(min, fits_t)
        maximums = map(max, fits_t)
        lenght = len(population)
        sums = map(sum, fits_t)
        sums2 = [sum(x*x for x in fit) for fit in fits_t]
        means = [sum_ / lenght for sum_ in sums]
        std_devs = [abs(sum2 / lenght - mean**2)**0.5 for sum2, mean in zip(sums2, means)]
        
        print "  Min %s" % ", ".join(map(str, minimums))
        print "  Max %s" % ", ".join(map(str, maximums))
        print "  Avg %s" % ", ".join(map(str, means))
        print "  Std %s" % ", ".join(map(str, std_devs))

    best_network = sn.SortingNetwork(INPUTS, hof[0])
    print best_network
    print best_network.draw()
    print "%i errors, length %i, depth %i" % hof[0].fitness.values

if __name__ == "__main__":
    main()
