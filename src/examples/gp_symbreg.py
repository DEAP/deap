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
import os
import random
import operator
import math
import itertools

sys.path.append(os.path.abspath('..'))

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.gp as gp
import eap.algorithms as algorithms

random.seed(2)

# Define new functions
def safeDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 0

prog_gen = gp.ProgramGenerator()
prog_gen.addPrimitive(operator.add, 2)
prog_gen.addPrimitive(operator.sub, 2)
prog_gen.addPrimitive(operator.mul, 2)
prog_gen.addPrimitive(safeDiv, 2)
prog_gen.addPrimitive(operator.neg, 1)
prog_gen.addPrimitive(math.cos, 1)
prog_gen.addPrimitive(math.sin, 1)
prog_gen.addTerminal(lambda: random.randint(-1,1))
prog_gen.addTerminal('x')

creator.create("Individual", (base.Tree,), {'fitness':base.Fitness})
creator.create("Population", (base.List,))

tools = toolbox.Toolbox()
tools.register('expr', prog_gen.generate, min=1, max=2)
tools.register('individual', creator.Individual, content=tools.expr)
tools.register('population', creator.Population, size=100, content=tools.individual)

def evalSymbReg(individual):
    if not individual.fitness.isValid():
        # Transform the tree expression in a callable function
        func = prog_gen.lambdify(individual, 'x')
        # Evaluate the sum of squared difference between the expression
        # and the real function : x**4 + x**3 + x**2 + x
        values = (x/10. for x in xrange(-10,10))
        diff_func = lambda x: (func(x)-(x**4 + x**3 + x**2 + x))**2
        diff = sum(map(diff_func, values))
        individual.fitness.append(diff)

tools.register('evaluate', evalSymbReg)
tools.register('select', toolbox.tournSel, tournsize=3)
tools.register('mate', toolbox.uniformOnePtTreeCx)
tools.register('mutate', toolbox.uniformTreeMut, expression=tools.expr,
		        min=0, max=2)

pop = tools.population()
algorithms.simpleEA(tools, pop, 0.5, 0.2, 50)

best = toolbox.bestSel(pop,1)[0]

print 'Best individual : ', gp.evaluate(best), best.fitness


