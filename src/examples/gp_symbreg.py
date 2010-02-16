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
import random

import eap.base as base
import eap.toolbox as toolbox
import eap.algorithms as algorithms

# define primitives
def add(left, right):
    return left + right
def sub(left, right):
    return left - right
def mul(left, right):
    return left * right
def rdiv(left, right):
    return sympy.nsimplify(left/right)

def randomCte():
    return random.randint(-1,1)

# add primitives and closures to their respective list
lFuncs = [add, sub, mul]
# defines symbols that will be used in the expression
lSymbols = [sympy.Symbol('x')]
# define terminal set
lTerms = [sympy.Rational(1)]
# add the symbols to the terminal set as 0-arity functions.
lTerms.extend([lambda: symb for symb in lSymbols])

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(-1.0,))
lTools.register('expression', base.expressionGenerator, funcSet=lFuncs,
		termSet=lTerms, maxDepth=3)
lTools.register('individual', base.IndividualTree,
                fitness=lTools.fitness, generator=lTools.expression())
lTools.register('population', base.Population, size=100,
                generator=lTools.individual)

def evalSymbReg(individual, symbols):
    if not individual.mFitness.isValid():
        # Simplify the expression by collecting the terms
        expr = individual.evaluate()
        # Transform the symbolic expression in a callable function
        lFuncExpr = sympy.lambdify(symbols, expr)
        lDiff = 0
        # Evaluate the sum of squared difference between the expression
        # and the real function : x**4 + x**3 + x**2 + x + 1
        for x in xrange(-10,10):
            x = x/10.
            try:
                lDiff += (lFuncExpr(x)-(x**4 + x**3 + x**2 + x + 1))**2
            except ZeroDivisionError:
                lDiff += ((x**4 + x**3 + x**2 + x + 1))**2

        individual.mFitness.append(lDiff)

lTools.register('evaluate', evalSymbReg, symbols=lSymbols)
lTools.register('select', toolbox.tournSel, tournSize=3)
lTools.register('mate', toolbox.uniformOnePtCxGP)
lTools.register('mutate', toolbox.uniformTreeMut, treeGenerator=lTools.expression,
		depthRange=(0,2))


lPop = lTools.population()
algorithms.simpleEA(lTools, lPop, 0.5, 0.2, 40)

lBest = toolbox.bestSel(lPop,1)[0]
print 'Best individual : ', sympy.sympify(lBest.evaluate()), lBest.mFitness