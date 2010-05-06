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
import csv

sys.path.append(os.path.abspath(".."))

import eap.base as base
import eap.creator as creator
import eap.toolbox as toolbox
import eap.gp as gp
import eap.algorithms as algorithms
import eap.halloffame as halloffame

logging.basicConfig(level=logging.DEBUG)

# Read the spam list features and put it in a list of lists.
# The dataset is from http://archive.ics.uci.edu/ml/datasets/Spambase
# This example is a copy of the OpenBEAGLE example :
# http://beagle.gel.ulaval.ca/refmanual/beagle/html/d2/dbe/group__Spambase.html
spamReader = csv.reader(open("spambase.csv"))
spam = list(list(float(elem) for elem in row) for row in spamReader)

# defined a new primitive set for strongly typed GP
pset = gp.TypedPrimitiveSet()

# boolean operators
pset.addPrimitive(operator.and_, "bool", ["bool", "bool"])
pset.addPrimitive(operator.or_, "bool", ["bool", "bool"])
pset.addPrimitive(operator.not_, "bool", ["bool"])

# floating point operators
# Define a safe division function
def safeDiv(left, right):
    try: return left / right
    except ZeroDivisionError: return 0

pset.addPrimitive(operator.add, "float", ["float","float"])
pset.addPrimitive(operator.sub, "float", ["float","float"])
pset.addPrimitive(operator.mul, "float", ["float","float"])
pset.addPrimitive(safeDiv, "float", ["float","float"])

# logic operators
# Define a new if-then-else function
def if_then_else(input, output1, output2):
    if input: return output1
    else: return output2

pset.addPrimitive(operator.lt, "bool", ["float", "float"])
pset.addPrimitive(operator.eq, "bool", ["float", "float"])
pset.addPrimitive(if_then_else, "float", ["bool", "float", "float"])

# terminals
pset.addEphemeralConstant(lambda: random.random() * 100, "float")
pset.addTerminal(0, "bool")
pset.addTerminal(1, "bool")
for i in xrange(57): pset.addTerminal("IN%s"%i, "float")

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", base.Tree, fitness=creator.FitnessMax)

tools = toolbox.Toolbox()
tools.register("expr", gp.generate_ramped_typed, type="bool", pset=pset, min=1, max=2)
tools.regInit("individual", creator.Individual, content=tools.expr)
tools.regInit("population", list, content=tools.individual, size=100)
tools.register("lambdify", gp.lambdify, pset=pset, args=["IN%s"%i for i in xrange(57)])

def evalSpambase(individual):
    # Transform the tree expression in a callable function
    func = tools.lambdify(expr=individual)
    # Randomly sample 400 mails in the spam database
    spam_samp = random.sample(spam, 400)
    # Evaluate the sum of correctly identified mail as spam
    result = sum(bool(func(*mail[:57])) is bool(mail[57]) for mail in spam_samp)
    return [result]
    
tools.register("evaluate", evalSpambase)
tools.register("select", toolbox.selTournament, tournsize=3)
tools.register("mate", toolbox.cxTypedTreeOnePoint)
tools.register("expr_mut", gp.generate_full_typed, pset=pset, min=0, max=2)
tools.register("mutate", toolbox.mutTypedTreeUniform, expr=tools.expr_mut)

pop = tools.population()
hof = halloffame.HallOfFame(1)

algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, halloffame=hof)

print "Best individual is %r\nwith fitness of %r" % (gp.evaluate(hof[0]), hof[0].fitness)
