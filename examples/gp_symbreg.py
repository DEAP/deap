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
import math
import logging

sys.path.append("..")

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.gp as gp
import eap.algorithms as algorithms
import eap.halloffame as halloffame

logging.basicConfig(level=logging.DEBUG)

random.seed(1348779701)

# Define new functions
def safeDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 0

pset = gp.PrimitiveSet()
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(safeDiv, 2)
pset.addPrimitive(operator.neg, 1)
pset.addPrimitive(math.cos, 1)
pset.addPrimitive(math.sin, 1)
pset.addEphemeralConstant(lambda: random.randint(-1,1))
pset.addTerminal('x')

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", base.Tree, fitness=creator.FitnessMin, pset=pset)

tools = toolbox.Toolbox()
tools.register("expr", gp.generate_ramped, pset=pset, min=1, max=2)
tools.register("individual", creator.Individual, content_init=tools.expr)
tools.register("population", list, content_init=tools.individual, size_init=100)
tools.register("lambdify", gp.lambdify, pset=pset, args='x')

def evalSymbReg(individual):
    # Transform the tree expression in a callable function
    
    func = tools.lambdify(expr=individual)
    # Evaluate the sum of squared difference between the expression
    # and the real function : x**4 + x**3 + x**2 + x
    values = (x/10. for x in xrange(-10,10))
    diff_func = lambda x: (func(x)-(x**4 + x**3 + x**2 + x))**2
    diff = sum(map(diff_func, values))
    return diff,

tools.register("evaluate", evalSymbReg)
tools.register("select", toolbox.selTournament, tournsize=3)
tools.register("mate", toolbox.cxTreeUniformOnePoint)
tools.register("expr_mut", gp.generate_full, min=0, max=2)
tools.register('mutate', toolbox.mutTreeUniform, expr=tools.expr_mut)

pop = tools.population()
hof = halloffame.HallOfFame(1)

algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, halloffame=hof)

logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
