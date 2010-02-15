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
import eap.algorithms as algorithms

#random.seed(2)

# Define new functions
def safeDiv(left, right):
    try:
        return left / right
    except ZeroDivisionError:
        return 0

def randomCte():
    return repr(random.randint(-1,1))

# define primitives
def add(left, right):
#    return "({0}+{1})".format(left,right) # compatible with Python 2.6.1 and Up
    return "(%s + %s)" % (str(left), str(right)) # compatible with Python 2.3 to 2.5.2
def sub(left, right):
#   return "({0}-{1})".format(left,right) # compatible with Python 2.6.1 and Up
    return "(%s - %s)" % (str(left), str(right))  # compatible with Python 2.3 to 2.5.2
def mul(left, right):
#    return "({0}*{1})".format(left,right) # compatible with Python 2.6.1 and Up
    return "(%s * %s)" % (str(left), str(right))  # compatible with Python 2.3 to 2.5.2
def div(left, right):
#    return "({0}/{1})".format(left,right) # compatible with Python 2.6.1 and Up
    return "safeDiv(%s,%s)" % (str(left), str(right)) # compatible with Python 2.3 to 2.5.2
def sinStr(right):
#    return "sin({0})".format(right) # compatible with Python 2.6.1 and Up
    return "sin(%s)" % str(right) # compatible with Python 2.3 to 2.5.2
def cosStr(right):
#    return "cos({0})".format(left,right) # compatible with Python 2.6.1 and Up
    return "cos(%s)" % str(right) # compatible with Python 2.3 to 2.5.2

# add primitives and closures to their respective list
lFuncs = [add, sub, mul, div, sinStr, cosStr]
#lFuncs = [add, sub, mul]
# defines symbols that will be used in the expression
lSymbols = ['x']
# define terminal set
lTerms = [1, randomCte]
# add the symbols to the terminal set
lTerms.extend(lSymbols)

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(-1.0,))
lTools.register('expression', base.expressionGenerator, funcSet=lFuncs,
		termSet=lTerms, maxDepth=3)
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

lTools.register('evaluate', evalSymbReg, symbols=lSymbols, functDict=locals())
lTools.register('select', toolbox.tournSel, tournSize=3)
lTools.register('crossover', toolbox.uniformOnePtCxGP)
lTools.register('mutate', toolbox.uniformTreeMut, treeGenerator=lTools.expression,
		depthRange=(0,2))

lPop = lTools.population()
algorithms.simpleGA(lTools, lPop, 0.5, 0.2, 100)

lBest = toolbox.bestSel(lPop,1)[0]
print lBest
print len(lBest)
print 'Best individual : ', sympy.sympify(lBest.evaluate()), lBest.mFitness