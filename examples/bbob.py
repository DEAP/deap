
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
import math
import random
import time

from itertools import chain

from deap import base
from deap import creator
from deap import benchmarks

import fgeneric
import bbobbenchmarks as bn

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode="d", fitness=creator.FitnessMin)

def update(individual, mu, sigma):
    """Update the current *individual* with values from a gaussian centered on
    *mu* and standard deviation *sigma*.
    """
    for i, mu_i in enumerate(mu):
        individual[i] = random.gauss(mu_i, sigma)

def tupleize(func):
    """A decorator that tuple-ize the result of a function. This is useful
    when the evaluation function returns a single value.
    """
    def wrapper(*args, **kargs):
        return func(*args, **kargs),
    return wrapper

def main(func, dim, maxfuncevals, ftarget=None):
    toolbox = base.Toolbox()
    toolbox.register("update", update)
    toolbox.register("evaluate", func)
    toolbox.decorate("evaluate", tupleize)
    
    # Create the desired optimal function value as a Fitness object
    # for later comparison
    opt = creator.FitnessMin((ftarget,))
    
    # Interval in which to initialize the optimizer
    interval = -5, 5
    sigma = (interval[1] - interval[0])/2.0
    alpha = 2.0**(1.0/dim)
    
    # Initialize best randomly and worst as a place holder
    best = creator.Individual(random.uniform(interval[0], interval[1]) for _ in range(dim))
    worst = creator.Individual([0.0] * dim)
    
    # Evaluate the first individual
    best.fitness.values = toolbox.evaluate(best)
    
    # Evolve until ftarget is reached or the number of evaluation
    # is exausted (maxfuncevals)
    for g in range(1, maxfuncevals):
        toolbox.update(worst, best, sigma)
        worst.fitness.values = toolbox.evaluate(worst)
        if best.fitness <= worst.fitness:
            # Incease mutation strength and swap the individual
            sigma = sigma * alpha
            best, worst = worst, best
        else:
            # Decrease mutation strength
            sigma = sigma * alpha**(-0.25)
        
        # Test if we reached the optimum of the function
        # Remember that ">" for fitness means better (not greater)
        if best.fitness > opt:
            return best
    
    return best

if __name__ == "__main__":
    # Maximum number of restart for an algorithm that detects stagnation
    maxrestarts = 1000
    
    # Create a COCO experiment that will log the results under the
    # ./output directory
    e = fgeneric.LoggingFunction("output")
    
    # Iterate over all desired test dimensions
    for dim in (2, 3, 5, 10, 20, 40):
        # Set the maximum number function evaluation granted to the algorithm
        # This is usually function of the dimensionality of the problem
        maxfuncevals = 100 * dim**2
        minfuncevals = dim + 2
        
        # Iterate over a set of benchmarks (noise free benchmarks here)
        for f_name in bn.nfreeIDs:
            
            # Iterate over all the instance of a single problem
            # Rotation, translation, etc.
            for instance in chain(range(1, 6), range(21, 31)):
                
                # Set the function to be used (problem) in the logger
                e.setfun(*bn.instantiate(f_name, iinstance=instance))
                
                # Independent restarts until maxfunevals or ftarget is reached
                for restarts in range(0, maxrestarts + 1):
                    if restarts > 0:
                        # Signal the experiment that the algorithm restarted
                        e.restart('independent restart')  # additional info
                    
                    # Run the algorithm with the remaining number of evaluations
                    revals = int(math.ceil(maxfuncevals - e.evaluations))
                    main(e.evalfun, dim, revals, e.ftarget)
                    
                    # Stop if ftarget is reached
                    if e.fbest < e.ftarget or e.evaluations + minfuncevals > maxfuncevals:
                        break
                
                e.finalizerun()
                
                print('f%d in %d-D, instance %d: FEs=%d with %d restarts, '
                      'fbest-ftarget=%.4e'
                      % (f_name, dim, instance, e.evaluations, restarts,
                         e.fbest - e.ftarget))
                         
            print('date and time: %s' % time.asctime())
