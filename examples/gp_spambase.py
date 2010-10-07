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
import random
import operator
import logging
import csv
import itertools

from eap import base
from eap import creator
from eap import toolbox
from eap import gp
from eap import algorithms
from eap import halloffame

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Read the spam list features and put it in a list of lists.
# The dataset is from http://archive.ics.uci.edu/ml/datasets/Spambase
# This example is a copy of the OpenBEAGLE example :
# http://beagle.gel.ulaval.ca/refmanual/beagle/html/d2/dbe/group__Spambase.html
spamReader = csv.reader(open("spambase.csv"))
spam = list(list(float(elem) for elem in row) for row in spamReader)

# defined a new primitive set for strongly typed GP
pset = gp.PrimitiveSetTyped("MAIN", itertools.repeat("float", 57), "bool", "IN")

# boolean operators
pset.addPrimitive(operator.and_, ["bool", "bool"], "bool")
pset.addPrimitive(operator.or_, ["bool", "bool"], "bool")
pset.addPrimitive(operator.not_, ["bool"], "bool")

# floating point operators
# Define a safe division function
def safeDiv(left, right):
    try: return left / right
    except ZeroDivisionError: return 0

pset.addPrimitive(operator.add, ["float","float"], "float")
pset.addPrimitive(operator.sub, ["float","float"], "float")
pset.addPrimitive(operator.mul, ["float","float"], "float")
pset.addPrimitive(safeDiv, ["float","float"], "float")

# logic operators
# Define a new if-then-else function
def if_then_else(input, output1, output2):
    if input: return output1
    else: return output2

pset.addPrimitive(operator.lt, ["float", "float"], "bool")
pset.addPrimitive(operator.eq, ["float", "float"], "bool")
pset.addPrimitive(if_then_else, ["bool", "float", "float"], "float")

# terminals
pset.addEphemeralConstant(lambda: random.random() * 100, "float")
pset.addTerminal(0, "bool")
pset.addTerminal(1, "bool")

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax, pset=pset)

tools = toolbox.Toolbox()
tools.register("expr", gp.generateRamped, pset=pset, type_=pset.ret, min_=1, max_=2)
tools.register("individual", creator.Individual, content_init=tools.expr)
tools.register("population", list, content_init=tools.individual, size_init=100)
tools.register("lambdify", gp.lambdify, pset=pset)

def evalSpambase(individual):
    # Transform the tree expression in a callable function
    func = tools.lambdify(expr=individual)
    # Randomly sample 400 mails in the spam database
    spam_samp = random.sample(spam, 400)
    # Evaluate the sum of correctly identified mail as spam
    result = sum(bool(func(*mail[:57])) is bool(mail[57]) for mail in spam_samp)
    return result,
    
tools.register("evaluate", evalSpambase)
tools.register("select", toolbox.selTournament, tournsize=3)
tools.register("mate", toolbox.cxTypedTreeOnePoint)
tools.register("expr_mut", gp.generateFull, min_=0, max_=2)
tools.register("mutate", toolbox.mutTypedTreeUniform, expr=tools.expr_mut)

if __name__ == "__main__":
    pop = tools.population()
    hof = halloffame.HallOfFame(1)
    
    algorithms.eaSimple(tools, pop, 0.5, 0.2, 40, halloffame=hof)
    
    logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
