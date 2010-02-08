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
#    return "({0}+{1})".format(left,right) # compatible with Python 2.6.1 and Up
     return "(%s + %s)" % (str(left), str(right)) # compatible with Python 2.3 to 2.5.2
def sub(left, right):
#    return "({0}-{1})".format(left,right) # compatible with Python 2.6.1 and Up
     return "(%s - %s)" % (str(left), str(right))  # compatible with Python 2.3 to 2.5.2
def mul(left, right):
#    return "({0}*{1})".format(left,right) # compatible with Python 2.6.1 and Up
     return "(%s * %s)" % (str(left), str(right))  # compatible with Python 2.3 to 2.5.2
def div(left, right):
#    return "({0}/{1})".format(left,right) # compatible with Python 2.6.1 and Up
     return "(%s / %s)" % (str(left), str(right)) # compatible with Python 2.3 to 2.5.2
def randomCte():
     return repr(random.randint(-1,1))

# add primitives and closures to their respective list
lFuncs = [add, sub, mul]
# defines symbols that will be used in the expression
lSymbols = ['x']
# define terminal set
lTerms = ['1']
# add the symbols to the terminal set
lTerms.extend(lSymbols)

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(-1.0,))
lTools.register('expression', base.expressionGenerator, funcSet=lFuncs,
		termSet=lTerms, maxDepth=3)
lTools.register('individual', base.Individual, size=1,
                fitness=lTools.fitness, generator=lTools.expression())
lTools.register('population', base.Population, size=100,
                generator=lTools.individual)

def evalSymbReg(individual, symbols):
    if not individual.mFitness.isValid():
	for expr in individual:
	    # Reduce the tree as one symbolic expression
	    lSymExpr = sympy.sympify(toolbox.evaluateExpr(expr))
	    # Transform the symbolic expression in a callable function
	    lFuncExpr = sympy.lambdify(symbols,lSymExpr)
	    lDiff = 0
	    # Evaluate the sum of squared difference between the expression
	    # and the real function : x**4 + x**3 + x**2 + x + 1
	    for x in xrange(-100,100):
		x = x/100.
		lDiff += (lFuncExpr(x)-(x**4 + x**3 + x**2 + x + 1))**2
	    individual.mFitness.append(lDiff)

lTools.register('evaluate', evalSymbReg, symbols=lSymbols)
lTools.register('select', toolbox.tournSel, tournSize=3)
lTools.register('crossover', toolbox.onePointCxGP)
lTools.register('mutate', toolbox.subTreeMut, treeGenerator=lTools.expression, 
		depthRange=(0,1))

lPop = lTools.population()
algorithms.simpleGA(lTools, lPop, 0.5, 0.2, 40)
print lPop[0]
print toolbox.evaluateExpr(lPop[0][0])
print sympy.collect(sympy.sympify(toolbox.evaluateExpr(lPop[0][0])), sympy.Symbol('x'))
