#!/usr/bin/env python2.7
#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

import csv
import logging
import random
import sys

import knn
from deap import algorithms
from deap import base
from deap import creator
from deap import operators
from deap import toolbox

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# kNN parameters
import knn
FILE="heart_scale.csv"
N_TRAIN=175
K=1

data = csv.reader(open(FILE, "rb"))
trainset = list()
trainlabels = list()
rows = [row for row in data]
random.shuffle(rows)
for row in rows:
    trainlabels.append(float(row[0]))
    trainset.append([float(e) for e in row[1:]])

classifier = knn.KNN(K)
classifier.train(trainset[:N_TRAIN], trainlabels[:N_TRAIN])

def evalClassifier(individual):
    labels = classifier.predict(trainset[N_TRAIN:], individual)
    return sum(1 for x, y in zip(labels, trainlabels) if x == y)  / float(len(trainlabels)), \
           sum(individual) / float(classifier.ndim)

creator.create("FitnessMulti", base.Fitness, weights=(1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMulti)

tools = toolbox.Toolbox()
# Attribute generator
tools.register("attr_bool", random.randint, 0, 1)
# Structure initializers
tools.register("individual", toolbox.fillRepeat, creator.Individual, tools.attr_bool, classifier.ndim)
tools.register("population", toolbox.fillRepeat, list, tools.individual)

# Operator registering
tools.register("evaluate", evalClassifier)
tools.register("mate", operators.cxUniform, indpb=0.1)
tools.register("mutate", operators.mutFlipBit, indpb=0.05)
tools.register("select", operators.selNSGA2)


def main():
    # random.seed(64)
    MU, LAMBDA = 100, 200
    pop = tools.population(n=MU)
    hof = operators.HallOfFame(1)
    stats = operators.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", operators.mean)
    stats.register("Std", operators.std_dev)
    stats.register("Min", min)
    stats.register("Max", max)

    algorithms.eaMuPlusLambda(tools, pop, mu=MU, lambda_=LAMBDA,
                              cxpb=0.5, mutpb=0.2, ngen=40, 
                              stats=stats, halloffame=hof)
    logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)
    
    return pop, stats, hof

if __name__ == "__main__":
    main()
