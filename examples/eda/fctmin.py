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

import random

import numpy

from operator import attrgetter

from deap import algorithms
from deap import base
from deap import benchmarks
from deap import creator
from deap import tools

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", numpy.ndarray, fitness=creator.FitnessMin) 

class EDA(object):
    def __init__(self, centroid, sigma, mu, lambda_):
        self.dim = len(centroid)
        self.loc = numpy.array(centroid)
        self.sigma = numpy.array(sigma)
        self.lambda_ = lambda_
        self.mu = mu
    
    def generate(self, ind_init):
        # Generate lambda_ individuals and put them into the provided class
        arz = self.sigma * numpy.random.randn(self.lambda_, self.dim) + self.loc
        return list(map(ind_init, arz))
    
    def update(self, population):
        # Sort individuals so the best is first
        sorted_pop = sorted(population, key=attrgetter("fitness"), reverse=True)
        
        # Compute the average of the mu best individuals
        z = sorted_pop[:self.mu] - self.loc
        avg = numpy.mean(z, axis=0)
        
        # Adjust variances of the distribution
        self.sigma = numpy.sqrt(numpy.sum((z - avg)**2, axis=0) / (self.mu - 1.0))
        self.loc = self.loc + avg

def main():
    N, LAMBDA = 30, 1000
    MU = int(LAMBDA/4)
    strategy = EDA(centroid=[5.0]*N, sigma=[5.0]*N, mu=MU, lambda_=LAMBDA)
    
    toolbox = base.Toolbox()
    toolbox.register("evaluate", benchmarks.rastrigin)
    toolbox.register("generate", strategy.generate, creator.Individual)
    toolbox.register("update", strategy.update)
    
    # Numpy equality function (operators.eq) between two arrays returns the
    # equality element wise, which raises an exception in the if similar()
    # check of the hall of fame. Using a different equality function like
    # numpy.array_equal or numpy.allclose solve this issue.
    hof = tools.HallOfFame(1, similar=numpy.array_equal)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    algorithms.eaGenerateUpdate(toolbox, ngen=150, stats=stats, halloffame=hof)
    
    return hof[0].fitness.values[0]

if __name__ == "__main__":
    main()
    


