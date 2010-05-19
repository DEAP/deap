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

sys.path.append("..")

import eap.algorithms as algorithms
import eap.base as base
import eap.cma as cma
import eap.creator as creator
import eap.halloffame as halloffame
import eap.toolbox as toolbox

logging.basicConfig(level=logging.DEBUG)
#random.seed(64)
# Seed is not needed here since cma use numpy.random ... This will be fixed in some 
# future release because it makes the results unreproductible from the main file
# (you can still fix the seed in cma.py)

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, fitness=creator.FitnessMin)

tools = toolbox.Toolbox()
# The first individual is set to a vector of 5.0 see http://www.lri.fr/~hansen/cmaes_inmatlab.html
# for more details about the rastrigin and other tests for CMA-ES
tools.regInit("individual", creator.Individual, content=lambda: 5.0, size=30, args=("d",))
tools.regInit("population", list, content=tools.individual, size=1)

tools.register("evaluate", cma.rastrigin)       # The rastrigin function is one
                                                # of the hardest function to optimize

pop = tools.population()                        # The CMA-ES algorithm takes a 
                                                # population of one individuals as argument

hof = halloffame.HallOfFame(1)

# The CMA-ES algorithm converge with good probability with those settings
cma.esCMA(tools, pop, sigma=5.0, ngen=250, lambda_=600, halloffame=hof)

logging.info("Best individual is %r", hof[0])
