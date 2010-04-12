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
import logging

sys.path.append(os.path.abspath('..'))

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.gp as gp
import eap.algorithms as algorithms

logging.basicConfig(level=logging.DEBUG)

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

pset = gp.PrimitiveSet()
pset.addPrimitive(operator.and_, 2)
pset.addPrimitive(operator.or_, 2)
pset.addPrimitive(operator.xor, 2)
pset.addPrimitive(operator.not_, 1)
pset.addTerminal(1)
pset.addTerminal(0)
for i in xrange(PARITY_FANIN_M):
    pset.addTerminal('IN%s'%i)

creator.create("Fitness", (base.Fitness,), {'weights':(1.0,)})
creator.create("Individual", (base.Tree,), {'fitness':creator.Fitness})
creator.create("Population", (base.List,))

tools = toolbox.Toolbox()
tools.register('expr_init', gp.generate_grow, pset=pset, min=1, max=2)
tools.register('individual', creator.Individual, content=tools.expr_init)
tools.register('population', creator.Population, size=500, content=tools.individual)
tools.register('lambdify', gp.lambdify, pset=pset, args=["IN%s" %i for i in xrange(PARITY_FANIN_M)])

def evalParity(individual):
    func = tools.lambdify(expr=individual)
    good = sum(func(*inputs[i]) == outputs[i] for i in xrange(PARITY_SIZE_M))
    return [good]

tools.register('evaluate', evalParity)
tools.register('select', toolbox.tournSel, tournsize=3)
tools.register('mate', toolbox.uniformOnePtTreeCx)
tools.register('expr_mut', gp.generate_grow, pset=pset, min=0, max=2)
tools.register('mutate', toolbox.uniformTreeMut, expr=tools.expr_mut)

pop = tools.population()

algorithms.simpleEA(tools, pop, 0.5, 0.2, 50)

best = toolbox.bestSel(pop,1)[0]
print 'Best individual : ', gp.evaluate(best), best.fitness
