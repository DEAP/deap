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
import random
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from deap import algorithms
from deap import base
from deap import benchmarks
from deap import creator
from deap import tools

IND_SIZE = 30

toolbox = base.Toolbox()

creator.create("Strategy", array.array, typecode='d')

toolbox.register("strategy", tools.fillRepeat, creator.Strategy, lambda: 1., IND_SIZE) 

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMin, strategy=toolbox.strategy)

# Attribute generator
toolbox.register("attr_float", random.uniform, -3, 3)

# Structure initializers
toolbox.register("individual", tools.fillRepeat, creator.Individual, toolbox.attr_float, IND_SIZE)
toolbox.register("population", tools.fillRepeat, list, toolbox.individual)
toolbox.register("mate", tools.cxESBlend, alpha=0.1, minstrategy=1e-10)
toolbox.register("mutate", tools.mutES, indpb=0.1, minstrategy=1e-10)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", benchmarks.sphere)

def main():
    random.seed(64)
    MU, LAMBDA = 8, 32
    pop = toolbox.population(n=MU)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", tools.mean)
    stats.register("Std", tools.std_dev)
    stats.register("Min", min)
    stats.register("Max", max)
    
    algorithms.eaMuCommaLambda(toolbox, pop, mu=MU, lambda_=LAMBDA, 
                               cxpb=0.6, mutpb=0.3, ngen=500, 
                               stats=stats, halloffame=hof)
    
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)
    
    return pop, stats, hof
    
if __name__ == "__main__":
    main()
