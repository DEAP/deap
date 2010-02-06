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
lTerms = [sympy.Symbol('x')]

lTools = toolbox.Toolbox()
lTools.register('fitness', base.Fitness, weights=(-1.0,))
lTools.register('expression', base.expressionGenerator, funcSet=lFuncs,
		termSet=lTerms, maxDepth=2)
lTools.register('individual', base.Individual, size=1,
                fitness=lTools.fitness, generator=lTools.expression())
lTools.register('population', base.Population, size=3,
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
	for x in xrange(-1000,1000):
	    x = x/1000.
	    lDiff += (lFuncExpr(x)-(x**2+x+1))**2
        individual.mFitness.append(lDiff)

lTools.register('evaluate', evalSymbReg, terms=lTerms)
lTools.register('select', toolbox.tournSel, tournSize=3)
#lTools.register('crossover', toolbox.twoPointsCx)
#lTools.register('mutate', toolbox.flipBitMut, flipIndxPb=0.05)


lPop = lTools.population()
map(lTools.evaluate, lPop)

lFitnesses = [lInd.mFitness[0] for lInd in lPop]
print 'Fitness'
print '\tMin Fitness :', min(lFitnesses)
print '\tMax Fitness :', max(lFitnesses)
print '\tMean Fitness :', sum(lFitnesses)/len(lFitnesses)
print 'Population'
for ind in lPop:
    print '\t', toolbox.evaluateExpr(ind[0]), ' : ', ind.mFitness

