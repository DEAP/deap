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

"""This example contains the evolving test from *Potter, M. and De Jong, K.,
2001, Cooperative Coevolution: An Architecture for Evolving Co-adapted
Subcomponents.* section 4.2.4. The number of species is evolved by adding and
removing species as stagnation occurs.
"""

import random
try:
    import matplotlib.pyplot as plt
    plt.figure()
except:
    plt = False

import numpy

from deap import algorithms
from deap import tools

import coop_base

IND_SIZE = coop_base.IND_SIZE
SPECIES_SIZE = coop_base.SPECIES_SIZE
NUM_SPECIES = 1
TARGET_SIZE = 30
IMPROVMENT_TRESHOLD = 0.5
IMPROVMENT_LENGTH = 5
EXTINCTION_TRESHOLD = 5.0

noise =      "*##*###*###*****##*##****#*##*###*#****##******##*#**#*#**######"
schematas = ("1##1###1###11111##1##1111#1##1###1#1111##111111##1#11#1#11######",
             "1##1###1###11111##1##1000#0##0###0#0000##000000##0#00#0#00######",
             "0##0###0###00000##0##0000#0##0###0#0000##001111##1#11#1#11######")

toolbox = coop_base.toolbox
toolbox.register("evaluateContribution", coop_base.matchSetContribution)

def main(extended=True, verbose=True):
    target_set = []
    species = []
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "species", "evals", "std", "min", "avg", "max"
    
    ngen = 300
    g = 0
    
    for i in range(len(schematas)):
        size = int(TARGET_SIZE/len(schematas))
        target_set.extend(toolbox.target_set(schematas[i], size))
    
    species = [toolbox.species() for _ in range(NUM_SPECIES)]
    species_index = list(range(NUM_SPECIES))
    last_index_added = species_index[-1]
    
    # Init with random a representative for each species
    representatives = [random.choice(species[i]) for i in range(NUM_SPECIES)]
    best_fitness_history = [None] * IMPROVMENT_LENGTH
    
    if plt and extended:
        contribs = [[]]
        stag_gen = []
        collab = []
    
    while g < ngen:
        # Initialize a container for the next generation representatives
        next_repr = [None] * len(species)
        for (i, s), j in zip(enumerate(species), species_index):
            # Vary the species individuals
            s = algorithms.varAnd(s, toolbox, 0.6, 1.0)
            
            # Get the representatives excluding the current species
            r = representatives[:i] + representatives[i+1:]
            for ind in s:
                # Evaluate and set the individual fitness
                ind.fitness.values = toolbox.evaluate([ind] + r, target_set)
            
            record = stats.compile(s)
            logbook.record(gen=g, species=j, evals=len(s), **record)
            
            if verbose: 
                print(logbook.stream)
            
            # Select the individuals
            species[i] = toolbox.select(s, len(s))  # Tournament selection
            next_repr[i] = toolbox.get_best(s)[0]   # Best selection
            
            if plt and extended:
                # Book keeping of the collaborative fitness
                collab.append(next_repr[i].fitness.values[0])
            
            g += 1
        
        representatives = next_repr
        
        # Keep representatives fitness for stagnation detection
        best_fitness_history.pop(0)
        best_fitness_history.append(representatives[0].fitness.values[0])
        
        try:
            diff = best_fitness_history[-1] - best_fitness_history[0]
        except TypeError:
            diff = float("inf")
        
        if plt and extended:
            for (i, rep), j in zip(enumerate(representatives), species_index):
                contribs[j].append((toolbox.evaluateContribution(representatives,
                    target_set, i)[0], g-1))
        
        if diff < IMPROVMENT_TRESHOLD:
            if len(species) > 1:
                contributions = []
                for i in range(len(species)):
                    contributions.append(toolbox.evaluateContribution(representatives, target_set, i)[0])
                
                for i in reversed(range(len(species))):
                    if contributions[i] < EXTINCTION_TRESHOLD:
                        species.pop(i)
                        species_index.pop(i)
                        representatives.pop(i)
            
            last_index_added += 1
            best_fitness_history = [None] * IMPROVMENT_LENGTH
            species.append(toolbox.species())
            species_index.append(last_index_added)
            representatives.append(random.choice(species[-1]))
            if extended and plt:
                stag_gen.append(g-1)
                contribs.append([])

    if extended:
        for r in representatives:
            # print final representatives without noise
            print("".join(str(x) for x, y in zip(r, noise) if y == "*"))
    
    if extended and plt:      # Ploting of the evolution
        line1, = plt.plot(collab, "--", color="k")
        
        for con in contribs:
            try:
                con, g = zip(*con)
                line2, = plt.plot(g, con, "-", color="k")
            except ValueError:
                pass
        
        axis = plt.axis("tight")
        
        for s in stag_gen:
            plt.plot([s, s], [0, axis[-1]], "--", color="k")
        
        plt.legend((line1, line2), ("Collaboration", "Contribution"), loc="center right")
        plt.xlabel("Generations")
        plt.ylabel("Fitness")
        plt.show()
    
if __name__ == "__main__":
    main()
