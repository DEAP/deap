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
import random
import logging

sys.path.append("..")

import eap.algorithms as algorithms
import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox

logging.basicConfig(level=logging.DEBUG)
random.seed(64)

creator.create("FitnessMax", (base.Fitness,), {"weights" : (1.0,)})
creator.create("Individual", (base.Array,), {"fitness" : creator.FitnessMax})
creator.create("Population", (base.List,))

tools = toolbox.Toolbox()
tools.register("individual", creator.Individual, size=100, typecode="b",
		content=lambda: random.randint(0, 1))
tools.register("population", creator.Population, size=300,
		content=tools.individual)

def evalOneMax(individual):
    return [sum(individual)]

tools.register("evaluate", evalOneMax)
tools.register("mate", toolbox.twoPointsCx)
tools.register("mutate", toolbox.flipBitMut, indpb=0.05)
tools.register("select", toolbox.tournSel, tournsize=3)

pop = tools.population()
algorithms.plusEA(tools, pop, 100, 100, 0.5, 0.2, 40)

