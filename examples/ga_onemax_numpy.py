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
import sys
import numpy
import random
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from deap import algorithms
from deap import base
from deap import creator
from deap import operators
from deap import toolbox

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", numpy.ndarray, fitness=creator.FitnessMax)

tools = toolbox.Toolbox()

tools.register("attr_bool", numpy.random.randint, 0, 2)
tools.register("individual", toolbox.fillRepeat, creator.Individual, tools.attr_bool, 100)
tools.register("population", toolbox.fillRepeat, list, tools.individual)

def evalOneMax(individual):
    return numpy.sum(individual),

tools.register("evaluate", evalOneMax)
tools.register("mate", operators.cxTwoPoints)
tools.register("mutate", operators.mutFlipBit, indpb=0.05)
tools.register("select", operators.selTournament, tournsize=3)

def main():
    random.seed(64)
    numpy.random.seed(11)
    
    pop = tools.population(n=300)
    hof = operators.HallOfFame(1)
    stats = operators.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", operators.mean)
    stats.register("Std", operators.std_dev)
    stats.register("Min", min)
    stats.register("Max", max)

    algorithms.eaSimple(tools, pop, cxpb=0.5, mutpb=0.2, ngen=40, stats=stats, halloffame=hof)
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)
    
    return pop, stats, hof

if __name__ == "__main__":
    main()
