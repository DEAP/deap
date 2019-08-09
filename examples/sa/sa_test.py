#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from sa import *

import numpy as np
import numpy.linalg as LA
from deap import base, creator, tools, algorithms

# Problem of Liear Regression
IND_SIZE = 3
N = 10
x = np.random.random(IND_SIZE)
A = 10*np.random.random((N, IND_SIZE))
b = A @ x + np.random.rand(N)/100

def evaluate(state):
    return LA.norm(A @ state-b),


creator.create("FitnessMin", base.Fitness, weights=(1,))
creator.create("Individual", np.ndarray, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("gene", np.random.random)
toolbox.register("state", tools.initRepeat, creator.Individual,
                 toolbox.gene, n=IND_SIZE)

toolbox.register("get_neighbour", tools.mutGaussian, mu=0, sigma=0.1, indpb=1)
toolbox.register("evaluate", evaluate)

stats = tools.Statistics(key=lambda s: s.fitness.values)
stats.register("value", lambda x: x[0])

s = toolbox.state()
s, logbook = annealing(s, toolbox=toolbox, initT=100, ngen=300, stats=stats, verbose=False)

print(f'Satisfied Solution(Error): {s} ({s.fitness.values[0]})')
print(f'Real Solution(Error): {x} ({LA.norm(A @ x-b)})')

import matplotlib.pyplot as plt
gen, value = logbook.select("gen", "value")
fig, ax = plt.subplots()
line = ax.plot(gen, value, "b-", label="误差")
ax.set_xlabel("ngen")
ax.set_ylabel("Error", color="b")
ax.set_title("Linear regression: ngen-error relation")
for tl in ax.get_yticklabels():
    tl.set_color("b")
plt.show()