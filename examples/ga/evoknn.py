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
import random

import numpy

import knn
from deap import algorithms
from deap import base
from deap import creator
from deap import tools

# kNN parameters
import knn
FILE="heart_scale.csv"
N_TRAIN=175
K=1

# Read data from file
with open(FILE, "r") as data_csv:
    data = csv.reader(data_csv)
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
    return sum(x == y for x, y in zip(labels, trainlabels[N_TRAIN:]))  / float(len(trainlabels[N_TRAIN:])), \
           sum(individual) / float(classifier.ndim)

creator.create("FitnessMulti", base.Fitness, weights=(1.0, -1.0))
creator.create("Individual", list, fitness=creator.FitnessMulti)

toolbox = base.Toolbox()
# Attribute generator
toolbox.register("attr_bool", random.randint, 0, 1)
# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, classifier.ndim)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# Operator registering
toolbox.register("evaluate", evalClassifier)
toolbox.register("mate", tools.cxUniform, indpb=0.1)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selNSGA2)


def main():
    # random.seed(64)
    MU, LAMBDA = 100, 200
    pop = toolbox.population(n=MU)
    hof = tools.ParetoFront()
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)
    
    pop, logbook = algorithms.eaMuPlusLambda(pop, toolbox, mu=MU, lambda_=LAMBDA,
                                             cxpb=0.7, mutpb=0.3, ngen=40, 
                                             stats=stats, halloffame=hof)
    
    return pop, logbook, hof

if __name__ == "__main__":
    main()
