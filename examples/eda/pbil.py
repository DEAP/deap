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

import array
import random

import numpy

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

class PBIL(object):
    def __init__(self, ndim, learning_rate, mut_prob, mut_shift, lambda_):
        self.prob_vector = [0.5] * ndim
        self.learning_rate = learning_rate
        self.mut_prob = mut_prob
        self.mut_shift = mut_shift
        self.lambda_ = lambda_

    def sample(self):
        return (random.random() < prob for prob in self.prob_vector)

    def generate(self, ind_init):
        return [ind_init(self.sample()) for _ in range(self.lambda_)]

    def update(self, population):
        best = max(population, key=lambda ind: ind.fitness)

        for i, value in enumerate(best):
            # Update the probability vector
            self.prob_vector[i] *= 1.0 - self.learning_rate
            self.prob_vector[i] += value * self.learning_rate

            # Mutate the probability vector
            if random.random() < self.mut_prob:
                self.prob_vector[i] *= 1.0 - self.mut_shift
                self.prob_vector[i] += random.randint(0, 1) * self.mut_shift

def evalOneMax(individual):
    return sum(individual),

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("evaluate", evalOneMax)

def main(seed):
    random.seed(seed)

    NGEN = 50

    #Initialize the PBIL EDA
    pbil = PBIL(ndim=50, learning_rate=0.3, mut_prob=0.1, 
                mut_shift=0.05, lambda_=20)

    toolbox.register("generate", pbil.generate, creator.Individual)
    toolbox.register("update", pbil.update)

    # Statistics computation
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    pop, logbook = algorithms.eaGenerateUpdate(toolbox, NGEN, stats=stats, verbose=True)

if __name__ == "__main__":
    main(seed=None)

