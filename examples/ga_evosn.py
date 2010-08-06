import sys
import random
import logging
import copy

sys.path.append("..")
logging.basicConfig(level=logging.DEBUG)

from itertools import permutations

from eap import algorithms
from eap import base
from eap import creator
from eap import halloffame
from eap import toolbox

class SortingNetwork(list):
    """Sorting network class.
    
    From Wikipedia : A sorting network is an abstract mathematical model
    of a network of wires and comparator modules that is used to sort a
    sequence of numbers. Each comparator connects two wires and sort the
    values by outputting the smaller value to one wire, and a larger
    value to the other.
    """
    def __init__(self, dimension, connectors = []):
        self.dimension = dimension
        for wire1, wire2 in connectors:
            self.addConnector(wire1, wire2)
    
    def addConnector(self, wire1, wire2):
        """Add a connector between wire1 and wire2 in the network."""
        if wire1 == wire2:
            return
        
        if wire1 > wire2:
            wire1, wire2 = wire2, wire1
        
        try:
            last_level = self[-1]
        except IndexError:
            # Empty network, create new level and connector
            self.append({wire1: wire2})
            return
        
        for wires in last_level.items():
            if wires[1] >= wire1 and wires[0] <= wire2:
                self.append({wire1: wire2})
                return
        
        last_level[wire1] = wire2
    
    def sort(self, values):
        """Sort the values in-place based on the connectors in the network."""
        for level in self:
            for wire1, wire2 in level.items():
                if values[wire1] > values[wire2]:
                    values[wire1], values[wire2] = values[wire2], values[wire1]
    
    def assess(self):
        """Test all possible inputs given the dimension of the network,
        and return the number of incorrectly sorted inputs.
        """
        ordered = range(self.dimension)
        misses = 0
        for sequence in permutations(ordered):
            sequence = list(sequence)
            self.sort(sequence)
            if ordered != sequence:
                misses += 1
        return misses
    
    def draw(self):
        """Return an ASCII representation of the network."""
        str_wires = [["-"]*7 * self.depth]
        str_wires[0][0] = "0"
        str_wires[0][1] = " o"
        str_spaces = []

        for i in xrange(1, self.dimension):
            str_wires.append(["-"]*7 * self.depth)
            str_spaces.append([" "]*7 * self.depth)
            str_wires[i][0] = str(i)
            str_wires[i][1] = " o"
        
        for index, level in enumerate(self):
            for wire1, wire2 in level.items():
                str_wires[wire1][(index+1)*6] = "x"
                str_wires[wire2][(index+1)*6] = "x"
                for i in xrange(wire1, wire2):
                    str_spaces[i][(index+1)*6+1] = "|"
                for i in xrange(wire1+1, wire2):
                    str_wires[i][(index+1)*6] = "|"
        
        network_draw = "".join(str_wires[0])
        for line, space in zip(str_wires[1:], str_spaces):
            network_draw += "\n"
            network_draw += "".join(space)
            network_draw += "\n"
            network_draw += "".join(line)
        return network_draw
    
    @property
    def depth(self):
        """Return the number of parallel steps that it takes to sort any input."""
        return len(self)
    
    @property
    def length(self):
        """Return the number of comparison-swap used."""
        return sum(len(level) for level in self)

inputs = 6

def evalEvoSN(individual, dimension):
    network = SortingNetwork(dimension, individual)
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
tools.register("network", genNetwork, dimension=inputs, min_size=9, max_size=12)

# Structure initializers
tools.register("individual", creator.Individual, content_init=tools.network)
tools.register("population", list, content_init=tools.individual, size_init=300)

tools.register("evaluate", evalEvoSN, dimension=inputs)
tools.register("mate", toolbox.cxTwoPoints)
tools.register("mutate", mutWire, dimension=inputs, indpb=0.05)
tools.register("addwire", mutAddWire, dimension=inputs)
tools.register("delwire", mutDelWire)

tools.register("select", toolbox.selTournament, tournsize=3)

def main():
    #random.seed(64)

    population = tools.population()
    hof = halloffame.HallOfFame(1)

    CXPB, MUTPB, ADDPB, DELPB, NGEN = 0.5, 0.2, 0.01, 0.01, 40
    
    # Evaluate the entire population
    for ind in population:
        ind.fitness.values = tools.evaluate(ind)
    
    # Begin the evolution
    for g in xrange(NGEN):
        print "-- Generation %i --" % g
        offsprings = [copy.deepcopy(ind) for ind in population]
    
        # Apply crossover and mutation
        for ind1, ind2 in zip(offsprings[::2], offsprings[1::2]):
            if random.random() < CXPB:
                tools.mate(ind1, ind2)
                del ind1.fitness.values
                del ind2.fitness.values
    
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
        for ind in offsprings:
            if not ind.fitness.valid:
                ind.fitness.values = tools.evaluate(ind)
        
        population = tools.select(population+offsprings, n=len(offsprings))
        hof.update(population)
        fits = [ind.fitness.values for ind in population]
        
        # Gather all the fitnesses in one list and print the stats
        fits_t = zip(*fits)             # Transpose fitnesses for analysis

        minimums = map(min, fits_t)
        maximums = map(max, fits_t)
        lenght = len(population)
        sums = map(sum, fits_t)
        sums2 = [sum(map(lambda x: x**2, fit)) for fit in fits_t]
        means = [sum_ / lenght for sum_ in sums]
        std_devs = [abs(sum2 / lenght - mean**2)**0.5 for sum2, mean in zip(sums2, means)]
        
        print "Min %s" % ", ".join(map(str, minimums))
        print "Max %s" % ", ".join(map(str, maximums))
        print "Avg %s" % ", ".join(map(str, means))
        print "Std %s" % ", ".join(map(str, std_devs))

    best = SortingNetwork(inputs, hof[0])
    print best
    print best.draw()

if __name__ == "__main__":
    main()