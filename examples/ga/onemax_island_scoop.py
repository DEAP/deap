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

from functools import partial

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

from scoop import futures

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_bool", random.randint, 0, 1)

# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, 100)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evalOneMax(individual):
    return sum(individual),

toolbox.register("evaluate", evalOneMax)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("map", futures.map)

def main():
    random.seed(64)
    NISLES = 5
    islands = [toolbox.population(n=300) for i in range(NISLES)]

    # Unregister unpicklable methods before sending the toolbox.
    toolbox.unregister("attr_bool")
    toolbox.unregister("individual")
    toolbox.unregister("population")

    NGEN, FREQ = 40, 5
    toolbox.register("algorithm", algorithms.eaSimple, toolbox=toolbox, 
                     cxpb=0.5, mutpb=0.2, ngen=FREQ, verbose=False)
    for i in range(0, NGEN, FREQ):
        results = toolbox.map(toolbox.algorithm, islands)
        islands = [pop for pop, logbook in results]
        tools.migRing(islands, 15, tools.selBest)

    return islands

if __name__ == "__main__":
    main()
