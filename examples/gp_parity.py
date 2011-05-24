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

from deap import algorithms
from deap import base
from deap import creator
from deap import gp
from deap import operators
from deap import toolbox

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
tools.register("individual", creator.Individual, toolbox.Iterate(tools.expr))
tools.register("population", list, toolbox.Repeat(tools.individual, 300))
tools.register("lambdify", gp.lambdify, pset=pset)

def evalParity(individual):
    func = tools.lambdify(expr=individual)
    good = sum(func(*inputs[i]) == outputs[i] for i in xrange(PARITY_SIZE_M))
    return good,

tools.register("evaluate", evalParity)
tools.register("select", operators.selTournament, tournsize=3)
tools.register("mate", operators.cxTreeUniformOnePoint)
tools.register("expr_mut", gp.generateGrow, min_=0, max_=2)
tools.register("mutate", operators.mutTreeUniform, expr=tools.expr_mut)

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    pop = tools.population()
    hof = operators.HallOfFame(1)
    stats = tools.clone(stats_t)
    
    algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, stats, halloffame=hof)
    
    logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
    
    return pop, stats, hof

if __name__ == "__main__":
    main()

