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

prog_gen = gp.ProgramGenerator()
prog_gen.addPrimitive(operator.and_, 2)
prog_gen.addPrimitive(operator.or_, 2)
prog_gen.addPrimitive(operator.xor, 2)
prog_gen.addPrimitive(operator.not_, 1)
prog_gen.addTerminal(1)
prog_gen.addTerminal(0)
prog_gen.addTerminal('IN0')
prog_gen.addTerminal('IN1')
prog_gen.addTerminal('IN2')
prog_gen.addTerminal('IN3')
prog_gen.addTerminal('IN4')
prog_gen.addTerminal('IN5')

creator.create("Fitness", (base.Fitness,), {'weights':(1.0,)})
creator.create("Individual", (base.Tree,), {'fitness':creator.Fitness})
creator.create("Population", (base.List,))

tools = toolbox.Toolbox()
tools.register('expr', prog_gen.generate, min=1, max=2)
tools.register('individual', creator.Individual, content=tools.expr)
tools.register('population', creator.Population, size=100, content=tools.individual)

def evalParity(individual):
    if not individual.fitness.isValid():
        func = prog_gen.lambdify(individual, ['IN0', 'IN1', 'IN2', 'IN3', 'IN4', 'IN5'])
        good = sum(func(*inputs[i]) == outputs[i] for i in xrange(PARITY_SIZE_M))
        individual.fitness.append(good)

tools.register('evaluate', evalParity)
tools.register('select', toolbox.tournSel, tournsize=3)
tools.register('mate', toolbox.uniformOnePtTreeCx)
tools.register('mutate', toolbox.uniformTreeMut, expression=tools.expr,
		        min=0, max=2)

pop = tools.population()

algorithms.simpleEA(tools, pop, 0.5, 0.2, 50)

best = toolbox.bestSel(pop,1)[0]
print 'Best individual : ', gp.evaluate(best), best.fitness
