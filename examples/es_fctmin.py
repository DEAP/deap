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
from eap import halloffame
from eap import toolbox

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

IND_SIZE = 30

tools = toolbox.Toolbox()

creator.create("Strategy", array.array)

tools.register("strategy", creator.Strategy, "d", content_init=lambda: 1., size_init=IND_SIZE) 

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, fitness=creator.FitnessMin, strategy=tools.strategy)

# Attribute generator
tools.register("attr_float", random.uniform, -3, 3)

# Structure initializers
tools.register("individual", creator.Individual, "d", content_init=tools.attr_float, size_init=IND_SIZE)
tools.register("population", list, content_init=tools.individual, size_init=50)

def evalSphere(individual):
    return sum(map(lambda x: x * x, individual)),
                   
tools.register("evaluate", evalSphere)
tools.register("mate", toolbox.cxESBlend, alpha=0.1, minstrategy=1e-10)
tools.register("mutate", toolbox.mutES, indpb=0.1, minstrategy=1e-10)
tools.register("select", toolbox.selTournament, tournsize=3)

if __name__ == "__main__":
    random.seed(64)
    
    pop = tools.population()
    hof = halloffame.HallOfFame(1)
    
    algorithms.eaMuCommaLambda(tools, pop, mu=8, lambda_=32, 
                               cxpb=0.6, mutpb=0.3, ngen=500, halloffame=hof)
    
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)
