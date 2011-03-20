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

import array
import sys
import random
import logging

from eap import algorithms
from eap import base
from eap import creator
from eap import operators
from eap import toolbox

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

IND_SIZE = 30

tools = toolbox.Toolbox()

creator.create("Strategy", array.array)

tools.register("strategy", creator.Strategy, "d", toolbox.Repeat(lambda: 1., IND_SIZE)) 

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, fitness=creator.FitnessMin, strategy=tools.strategy)

# Attribute generator
tools.register("attr_float", random.uniform, -3, 3)

# Structure initializers
tools.register("individual", creator.Individual, "d", toolbox.Repeat(tools.attr_float, IND_SIZE))
tools.register("population", list, toolbox.Repeat(tools.individual, 50))

def evalSphere(individual):
    return sum(map(lambda x: x * x, individual)),
                   
tools.register("evaluate", evalSphere)
tools.register("mate", operators.cxESBlend, alpha=0.1, minstrategy=1e-10)
tools.register("mutate", operators.mutES, indpb=0.1, minstrategy=1e-10)
tools.register("select", operators.selTournament, tournsize=3)

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    random.seed(64)
    
    pop = tools.population()
    hof = operators.HallOfFame(1)
    stats = tools.clone(stats_t)
    
    algorithms.eaMuCommaLambda(tools, pop, mu=8, lambda_=32, 
                               cxpb=0.6, mutpb=0.3, ngen=500, 
                               stats=stats, halloffame=hof)
    
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)
    
    return pop, stats, hof
    
if __name__ == "__main__":
    main()
