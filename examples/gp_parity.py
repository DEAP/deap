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
import operator
import logging

from eap import base
from eap import creator
from eap import toolbox
from eap import gp
from eap import algorithms
from eap import halloffame

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Initialize Parity problem input and output matrices
PARITY_FANIN_M = 6
PARITY_SIZE_M = 2**PARITY_FANIN_M

inputs = [None] * PARITY_SIZE_M
outputs = [None] * PARITY_SIZE_M

for i in xrange(PARITY_SIZE_M):
    inputs[i] = [None] * PARITY_FANIN_M
    value = i
    dividor = PARITY_SIZE_M
    parity = 1
    for j in xrange(PARITY_FANIN_M):
        dividor /= 2
        if value >= dividor:
            inputs[i][j] = 1
            parity = int(not parity)
            value -= dividor
        else:
            inputs[i][j] = 0
    outputs[i] = parity

pset = gp.PrimitiveSet("MAIN", PARITY_FANIN_M, "IN")
pset.addPrimitive(operator.and_, 2)
pset.addPrimitive(operator.or_, 2)
pset.addPrimitive(operator.xor, 2)
pset.addPrimitive(operator.not_, 1)
pset.addTerminal(1)
pset.addTerminal(0)

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)

tools = toolbox.Toolbox()
tools.register("expr", gp.generateFull, pset=pset, min_=3, max_=5)
tools.register("individual", creator.Individual, content_init=tools.expr)
tools.register("population", list, content_init=tools.individual, size_init=300)
tools.register("lambdify", gp.lambdify, pset=pset)

def evalParity(individual):
    func = tools.lambdify(expr=individual)
    good = sum(func(*inputs[i]) == outputs[i] for i in xrange(PARITY_SIZE_M))
    return good,

tools.register("evaluate", evalParity)
tools.register("select", toolbox.selTournament, tournsize=3)
tools.register("mate", toolbox.cxTreeUniformOnePoint)
tools.register("expr_mut", gp.generateGrow, min_=0, max_=2)
tools.register("mutate", toolbox.mutTreeUniform, expr=tools.expr_mut)

if __name__ == "__main__":

    pop = tools.population()
    hof = halloffame.HallOfFame(1)
    
    algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, halloffame=hof)
    
    logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
