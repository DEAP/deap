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

def if_then_else(condition, out1, out2):
    return out1 if condition else out2

# Initialize Multiplexer problem input and output vectors

MUX_SELECT_LINES = 3
MUX_IN_LINES = 2 ** MUX_SELECT_LINES
MUX_TOTAL_LINES = MUX_SELECT_LINES + MUX_IN_LINES

inputs = [[0] * MUX_TOTAL_LINES for i in range(2 ** MUX_TOTAL_LINES)]
outputs = [None] * (2 ** MUX_TOTAL_LINES)

for i in range(2 ** MUX_TOTAL_LINES):
    value = i
    dividor = 2 ** MUX_TOTAL_LINES
    for j in range(MUX_TOTAL_LINES):
        dividor /= 2
        if value >= dividor:
            inputs[i][j] = 1
            value -= dividor
            
    indexOutput = 3
    if inputs[i][0]:
        indexOutput += 1
    if inputs[i][1]:
        indexOutput += 2
    if inputs[i][2]:
        indexOutput += 4    
    outputs[i] = inputs[i][indexOutput]

pset = gp.PrimitiveSet("MAIN", MUX_TOTAL_LINES, "IN")
pset.addPrimitive(operator.and_, 2)
pset.addPrimitive(operator.or_, 2)
pset.addPrimitive(operator.not_, 1)
pset.addPrimitive(if_then_else, 3)
pset.addTerminal(1)
pset.addTerminal(0)

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)

tools = toolbox.Toolbox()
tools.register("expr", gp.generateFull, pset=pset, min_=2, max_=4)
tools.register("individual", creator.Individual, toolbox.Iterate(tools.expr))
tools.register("population", list, toolbox.Repeat(tools.individual, 800))
tools.register("lambdify", gp.lambdify, pset=pset)

def evalMultiplexer(individual):
    func = tools.lambdify(expr=individual)
    good = sum((func(*(inputs[i])) == outputs[i] for i in range(2 ** MUX_TOTAL_LINES)))
    return good / float(2 ** MUX_TOTAL_LINES),

tools.register("evaluate", evalMultiplexer)
tools.register("select", operators.selTournament, tournsize=7)
tools.register("mate", operators.cxTreeUniformOnePoint)
tools.register("expr_mut", gp.generateGrow, min_=0, max_=2)
tools.register("mutate", operators.mutTreeUniform, expr=tools.expr_mut)

stats_t = operators.Stats(lambda ind: ind.fitness.values)
stats_t.register("Avg", operators.mean)
stats_t.register("Std", operators.std_dev)
stats_t.register("Min", min)
stats_t.register("Max", max)

def main():
    random.seed()
    pop = tools.population()
    hof = operators.HallOfFame(1)
    stats = tools.clone(stats_t)
    
    algorithms.eaSimple(tools, pop, 0.8, 0.1, 40, stats, halloffame=hof)
    
    logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
    
    return pop, stats, hof

if __name__ == "__main__":
    main()

