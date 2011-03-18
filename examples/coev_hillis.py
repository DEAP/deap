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
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

import random

import sortingnetwork as sn
from eap import algorithms
from eap import base
from eap import creator
from eap import halloffame
from eap import statistics
from eap import toolbox

INPUTS = 12

def evalNetwork(host, parasite, dimension):
    network = sn.SortingNetwork(dimension, host)
    return network.assess(parasite),

def genWire(dimension):
    return (random.randrange(dimension), random.randrange(dimension))

def genNetwork(dimension, min_size, max_size):
    size = random.randint(min_size, max_size)
    return [genWire(dimension) for i in xrange(size)]

def getParasite(dimension):
    return [random.choice((0, 1)) for i in range(dimension)]

def mutNetwork(individual, dimension, mutpb, addpb, delpb, indpb):
    if random.random() < mutpb:
        for index, elem in enumerate(individual):
            if random.random() < indpb:
                individual[index] = genWire(dimension)
    if random.random() < addpb:
        index = random.randint(0, len(individual))
        individual.insert(index, genWire(dimension))
    if random.random() < delpb:
        index = random.randrange(len(individual))
        del individual[index]
    return individual

def mutParasite(individual, indmut, indpb):
    for i in individual:
        if random.random() < indpb:
            indmut(i)
    return individual

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Host", list, fitness=creator.FitnessMin)
creator.create("Parasite", list, fitness=creator.FitnessMax)

htools = toolbox.Toolbox()
ptools = toolbox.Toolbox()

htools.register("network", genNetwork, dimension=INPUTS, min_size=9, max_size=12)
htools.register("individual", creator.Host, toolbox.Iterate(htools.network))
htools.register("population", list, toolbox.Repeat(htools.individual, 3000))

ptools.register("parasite", getParasite, dimension=INPUTS)
ptools.register("individual", creator.Parasite, toolbox.Repeat(ptools.parasite, 20))
ptools.register("population", list, toolbox.Repeat(ptools.individual, 3000))

htools.register("evaluate", evalNetwork, dimension=INPUTS)
htools.register("mate", toolbox.cxTwoPoints)
htools.register("mutate", mutNetwork, dimension=INPUTS, mutpb=0.2, addpb=0.01, 
    delpb=0.01, indpb=0.05)
htools.register("select", toolbox.selTournament, tournsize=3)

ptools.register("mate", toolbox.cxTwoPoints)
ptools.register("indMutate", toolbox.mutFlipBit, indpb=0.05)
ptools.register("mutate", mutParasite, indmut=ptools.indMutate, indpb=0.05)
ptools.register("select", toolbox.selTournament, tournsize=3)

stats_t = statistics.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", statistics.mean)
stats_t.register("Std", statistics.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    random.seed(64)
    
    hosts = htools.population()
    parasites = ptools.population()
    hof = halloffame.HallOfFame(1)
    hstats = htools.clone(stats_t)
    
    MAXGEN = 50
    H_CXPB, H_MUTPB = 0.5, 0.3
    P_CXPB, P_MUTPB = 0.5, 0.3
    
    fits = htools.map(htools.evaluate, hosts, parasites)
    for host, parasite, fit in zip(hosts, parasites, fits):
        host.fitness.values = parasite.fitness.values = fit
    
    hof.update(hosts)
    hstats.update(hosts)
    
    for g in range(MAXGEN):
        print "-- Generation %i --" % g
        hosts = htools.select(hosts, len(hosts))
        hosts = [htools.clone(ind) for ind in hosts]
        parasites = ptools.select(parasites, len(parasites))
        parasites = [ptools.clone(ind) for ind in parasites]
        
        hosts = algorithms.varSimple(htools, hosts, H_CXPB, H_MUTPB)
        parasites = algorithms.varSimple(ptools, parasites, P_CXPB, P_MUTPB)
        
        fits = htools.map(htools.evaluate, hosts, parasites)
        for host, parasite, fit in zip(hosts, parasites, fits):
            host.fitness.values = parasite.fitness.values = fit
        
        hof.update(hosts)
        hstats.update(hosts)
        
        for key, stat in hstats.data.items():
            print "  %s %s" % (key, ", ".join(map(str, stat[-1])))
    
    best_network = sn.SortingNetwork(INPUTS, hof[0])
    print best_network
    print best_network.draw()
    print "%i errors" % best_network.assess()

    return hosts, hstats, hof

if __name__ == "__main__":
    main()