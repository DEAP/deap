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

import sympy
import sys
import os
import random
from math import cos, sin

sys.path.append(os.path.abspath('..'))

import eap.base as base
import eap.toolbox as toolbox
import eap.gptoolbox as gptoolbox
import eap.algorithms as algorithms

#random.seed(2)

# Define new functions
def safeDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 0
def randomCte():
    return random.randint(-1,1)

lToolsGP = gptoolbox.ToolboxGP()
lToolsGP.addOperation('add', '+', 'binary')
lToolsGP.addOperation('sub', '-', 'binary')
lToolsGP.addOperation('mul', '*', 'binary')
lToolsGP.addOperation('neg', '-', 'unary')
lToolsGP.addFunction(safeDiv)
lToolsGP.addFunction(cos,1)
lToolsGP.addFunction(sin,1)
lToolsGP.addTerminal(randomCte)
lToolsGP.addTerminal(1)
lToolsGP.addSymbol('x')

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(-1.0,))
lTools.register('expression', base.expressionGenerator, funcSet=lToolsGP.mPrimitiveSet,
		termSet=lToolsGP.mTerminalSet, maxDepth=3)
lTools.register('individual', base.IndividualTree,
                fitness=lTools.fitness, generator=lTools.expression())
lTools.register('population', base.Population, size=100,
                generator=lTools.individual)

def evalSymbReg(individual, symbols, functDict):
    if not individual.mFitness.isValid():
        expr = individual.evaluate()
        # Transform the symbolic expression in a callable function
        lFuncExpr = sympy.lambdify(symbols, expr, functDict)
        lDiff = 0
        # Evaluate the sum of squared difference between the expression
        # and the real function : x**4 + x**3 + x**2 + x
        for x in xrange(-10,10):
            x = x/10.
            lDiff += (lFuncExpr(x)-(x**4 + x**3 + x**2 + x))**2
        individual.mFitness.append(lDiff)

lTools.register('evaluate', evalSymbReg, symbols=lToolsGP.mSymbolSet, functDict=lToolsGP.mFuncDict)
lTools.register('select', toolbox.tournSel, tournSize=3)
lTools.register('mate', toolbox.uniformOnePtCxGP)
lTools.register('mutate', toolbox.uniformTreeMut, treeGenerator=lTools.expression,
		depthRange=(0,2))

lPop = lTools.population()
algorithms.simpleEA(lTools, lPop, 0.5, 0.2, 50)

lBest = toolbox.bestSel(lPop,1)[0]
print 'Best individual : ', sympy.sympify(lBest.evaluate()), lBest.mFitness