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

"""Implementation of the Dynamic Differential Evolution algorithm as presented
in *Mendes and Mohais, 2005, DynDE: A Differential Evolution for Dynamic
Optimization Problems.*
"""

import array
import itertools
import math
import operator
import random

import numpy

from deap import base
from deap.benchmarks import movingpeaks
from deap import creator
from deap import tools

scenario = movingpeaks.SCENARIO_2

NDIM = 5
BOUNDS = [scenario["min_coord"], scenario["max_coord"]]

mpb = movingpeaks.MovingPeaks(dim=NDIM, **scenario)

def brown_ind(iclass, best, sigma):
    return iclass(random.gauss(x, sigma) for x in best)

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, typecode='d', fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("attr_float", random.uniform, BOUNDS[0], BOUNDS[1])
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, NDIM)
toolbox.register("brownian_individual", brown_ind, creator.Individual, sigma=0.3)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("select", random.sample, k=4)
toolbox.register("best", tools.selBest, k=1)
toolbox.register("evaluate", mpb)

def main(verbose=True):
    NPOP = 10   # Should be equal to the number of peaks
    CR = 0.6
    F = 0.4
    regular, brownian = 4, 2

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "error", "offline_error", "avg", "max"

    # Initialize populations
    populations = [toolbox.population(n=regular + brownian) for _ in range(NPOP)]

    # Evaluate the individuals
    for idx, subpop in enumerate(populations):
        fitnesses = toolbox.map(toolbox.evaluate, subpop)
        for ind, fit in zip(subpop, fitnesses):
            ind.fitness.values = fit

    record = stats.compile(itertools.chain(*populations))
    logbook.record(gen=0, evals=mpb.nevals, error=mpb.currentError(),
                   offline_error=mpb.offlineError(), **record)
    if verbose:
        print(logbook.stream)

    g = 1
    while mpb.nevals < 5e5:
        # Detect a change and invalidate fitnesses if necessary
        bests = [toolbox.best(subpop)[0] for subpop in populations]
        if any(b.fitness.values != toolbox.evaluate(b) for b in bests):
            for individual in itertools.chain(*populations):
                del individual.fitness.values

        # Apply exclusion
        rexcl = (BOUNDS[1] - BOUNDS[0]) / (2 * NPOP**(1.0/NDIM))
        for i, j in itertools.combinations(range(NPOP), 2):
            if bests[i].fitness.valid and bests[j].fitness.valid:
                d = sum((bests[i][k] - bests[j][k])**2 for k in range(NDIM))
                d = math.sqrt(d)

                if d < rexcl:
                    if bests[i].fitness < bests[j].fitness:
                        k = i
                    else:
                        k = j

                    populations[k] = toolbox.population(n=regular + brownian)
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in itertools.chain(*populations) if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        record = stats.compile(itertools.chain(*populations))
        logbook.record(gen=g, evals=mpb.nevals, error=mpb.currentError(),
                       offline_error=mpb.offlineError(), **record)
        if verbose:
            print(logbook.stream)

        # Evolve the sub-populations
        for idx, subpop in enumerate(populations):
            newpop = []
            xbest, = toolbox.best(subpop)
            # Apply regular DE to the first part of the population
            for individual in subpop[:regular]:
                x1, x2, x3, x4 = toolbox.select(subpop)
                offspring = toolbox.clone(individual)
                index = random.randrange(NDIM)
                for i, value in enumerate(individual):
                    if i == index or random.random() < CR:
                        offspring[i] = xbest[i] + F * (x1[i] + x2[i] - x3[i] - x4[i])
                offspring.fitness.values = toolbox.evaluate(offspring)
                if offspring.fitness >= individual.fitness:
                    newpop.append(offspring)
                else:
                    newpop.append(individual)

            # Apply Brownian to the last part of the population
            newpop.extend(toolbox.brownian_individual(xbest) for _ in range(brownian))

            # Evaluate the brownian individuals
            for individual in newpop[-brownian:]:
                individual.fitness.value = toolbox.evaluate(individual)

            # Replace the population 
            populations[idx] = newpop

        g += 1

    return logbook

if __name__ == "__main__":
    main()
