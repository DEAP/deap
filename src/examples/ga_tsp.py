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
import logging
import random
import yaml

sys.path.append("..")

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.algorithms as algorithms

logging.basicConfig(level=logging.INFO)
random.seed(1638)

# gr*.yml contains the distance map in list of list style in YAML/JSON format
# Optimal solutions are : gr17 = 2085, gr24 = 1272, gr120 = 6942
distance_map = yaml.load(open("gr17.yml", "r"))
IND_SIZE = len(distance_map[0])

creator.create("Individual", (base.Indices,), {"fitness" : base.Fitness})
creator.create("Population", (base.List,))

tools = toolbox.Toolbox()
tools.register("individual", creator.Individual, size=IND_SIZE)
tools.register("population", creator.Population, size=300, content=tools.individual)

def evalTSP(individual):
    distance = distance_map[individual[-1]][individual[0]]
    for gene1, gene2 in zip(individual[0:-1], individual[1:]):
        distance += distance_map[gene1][gene2]
    return [distance]

tools.register("mate", toolbox.pmCx)
tools.register("mutate", toolbox.shuffleIndxMut, indpb=0.05)
tools.register("select", toolbox.tournSel, tournsize=3)
tools.register("evaluate", evalTSP)

pop = tools.population()

algorithms.simpleEA(tools, pop, 0.5, 0.2, 50)

best_ind = toolbox.bestSel(pop, 1)[0]
logging.info("Best individual is %s", str(best_ind))
logging.info("Best individual has fitness of %s", str(best_ind.fitness))
