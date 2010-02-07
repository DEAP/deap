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

import eap.base as base
import eap.toolbox as toolbox
import eap.algorithms as algorithms

# define primitives
def add(left, right):
    return sympy.Add(left,right)
def sub(left, right):
    return sympy.Add(left, sympy.Mul(right,sympy.Rational(-1)))
def mul(left, right):
    return sympy.Mul(left, right)
def div(left, right):
    return sympy.Mul(left, sympy.Pow(right, sympy.Rational(-1)))

# add primitives and closures to their respective list
lFuncs = [add, sub, mul]
lSymbols = [sympy.Symbol('x')]
lTerms = [sympy.Rational(1)]
lTerms.extend(lSymbols)

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(-1.0,))
lTools.register('expression', base.expressionGenerator, funcSet=lFuncs,
		termSet=lTerms, maxDepth=2)
lTools.register('individual', base.Individual, size=1,
                fitness=lTools.fitness, generator=lTools.expression())
lTools.register('population', base.Population, size=100,
                generator=lTools.individual)

def evalSymbReg(individual, terms):
    if not individual.mFitness.isValid():
	# Reduce the tree as one symbolic expression
	lSymExpr = toolbox.evaluateExpr(individual[0])
	# Transform the symbolic expression in a callable function
	lFuncExpr = sympy.lambdify(terms,lSymExpr)
	lDiff = 0
	# Evaluate the sum of squared difference between the expression
	# and the real function : x**2 + x + 1
	for x in xrange(-100,100):
	    x = x/100.
	    lDiff += abs(lFuncExpr(x)-(x**2+x+1))
        individual.mFitness.append(lDiff)

lTools.register('evaluate', evalSymbReg, terms=lSymbols)
lTools.register('select', toolbox.tournSel, tournSize=3)
lTools.register('crossover', toolbox.onePointCxGP)
lTools.register('mutate', toolbox.subTreeMut, treeGenerator=lTools.expression, 
		depthRange=(0,1))

lPop = lTools.population()
algorithms.simpleGA(lTools, lPop, 0.5, 0.2, 40)
for ind in lPop:
    if ind.mFitness[0] < 1.:
	print toolbox.evaluateExpr(ind[0])