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
random.seed(64)     # Random must be seeded before importing cma because it is
                    # used to seed numpy.random
                    # This will be fixed in future release.

from eap import algorithms
from eap import base
from eap import cma
from eap import creator
from eap import halloffame
from eap import toolbox

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, fitness=creator.FitnessMin)

tools = toolbox.Toolbox()
# The first individual is set to a vector of 5.0 see http://www.lri.fr/~hansen/cmaes_inmatlab.html
# for more details about the rastrigin and other tests for CMA-ES
tools.register("individual", creator.Individual, "d", content_init=lambda: 5.0, size_init=30)
tools.register("population", list, content_init=tools.individual, size_init=1)

def evalCMA(ind):
    return cma.rastrigin(ind),

# The rastrigin function is one of the hardest function to optimize
tools.register("evaluate", evalCMA)

if __name__ == "__main__":
    # The CMA-ES algorithm takes a population of one individual as argument
    pop = tools.population()
    
    hof = halloffame.HallOfFame(1)
    
    # The CMA-ES algorithm converge with good probability with those settings
    cma.esCMA(tools, pop, sigma=5.0, ngen=250, lambda_=600, halloffame=hof)
    
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)
