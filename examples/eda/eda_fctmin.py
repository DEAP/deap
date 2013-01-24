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
from operator import attrgetter
import numpy

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

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", tools.mean)
    stats.register("std", tools.std)
    stats.register("min", min)
    stats.register("max", max)
    
    algorithms.eaGenerateUpdate(toolbox, ngen=150, stats=stats, halloffame=hof)
    
    return hof[0].fitness.values[0]

if __name__ == "__main__":
    main()
    


