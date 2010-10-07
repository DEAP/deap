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

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

from eap import algorithms
from eap import base
from eap import creator
from eap import halloffame
from eap import toolbox

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, fitness=creator.FitnessMax)

tools = toolbox.Toolbox()

# Attribute generator
tools.register("attr_bool", random.randint, 0, 1)

# Structure initializers
tools.register("individual", creator.Individual, "b", content_init=tools.attr_bool, size_init=100)
tools.register("population", list, content_init=tools.individual, size_init=300)

def evalOneMax(individual):
    return sum(individual),

tools.register("evaluate", evalOneMax)
tools.register("mate", toolbox.cxTwoPoints)
tools.register("mutate", toolbox.mutFlipBit, indpb=0.05)
tools.register("select", toolbox.selTournament, tournsize=3)

def main():
    random.seed(64)
    
    pop = tools.population()
    hof = halloffame.HallOfFame(1)

    algorithms.eaSimple(tools, pop, cxpb=0.5, mutpb=0.2, ngen=40, halloffame=hof)
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)

if __name__ == "__main__":
    main()
