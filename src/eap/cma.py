
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
#
#    Copyright 2010, Francois-Michel De Rainville and Felix-Antoine Fortin.
#    Special thanks to Nikolaus Hansen for providing major part of this code.
#    

import copy
import logging
import math
import random
import numpy
    
_logger = logging.getLogger("eap.cma")
    
def cmaES(toolbox, population, sigma, ngen, **kargs):
    """The CMA-ES algorithm as described in Hansen, N. (2006). *The CMA
    Evolution Strategy: A Comparing Rewiew.*
    
    The provided *population* should be a list of one or more individuals. The
    other keyworded arguments are passed to the class :class:`CMAStrategy`.
    """
    _logger.info("Start of evolution")
    strategy = CMAStrategy(population, sigma, kargs)  # Initialize the strategy
    
    for g in xrange(ngen):
        _logger.info("Evolving generation %i", g)
        
        # Replace the whole population with the generated individuals from the
        # cma strategy
        population[:] = strategy.generate()
        
        # Evaluate the individuals
        for ind in population:
            ind.fitness.extend(toolbox.evaluate(ind))
        
        # Update the Strategy with the evaluated individuals
        strategy.update(population)
        
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness[0] for ind in population]
        _logger.debug("Min %f", min(fits))
        _logger.debug("Max %f", max(fits))
        lenght = len(population)
        mean = sum(fits) / lenght
        sum2 = sum(map(lambda x: x**2, fits))
        std_dev = (sum2 / lenght - mean**2)**0.5
        _logger.debug("Mean %f", mean)
        _logger.debug("Std. Dev. %f", std_dev)
        
    _logger.info("End of (successful) evolution")
    

class CMAStrategy(object):
    """
    Additional configuration may be passed throught the *params* argument as a 
    dictionary,
    
    +----------------+---------------------------+----------------------------+
    | Parameter      | Default                   | Details                    |
    +================+===========================+============================+
    | ``lambda_``    | ``floor(4 + 3 * log(N))`` | Number of children to      |
    |                |                           | produce at each generation,|
    |                |                           | ``N`` is the individual's  |
    |                |                           | size.                      |
    +----------------+---------------------------+----------------------------+
    | ``mu``         | ``floor(lambda_ / 2)``    | The number of parents to   | 
    |                |                           | keep from the              |
    |                |                           | lambda children.           |
    +----------------+---------------------------+----------------------------+
    | ``weights``    | ``"superlinear"``         | Decrease speed, can be     |
    |                |                           | ``"superlinear"``,         |
    |                |                           | ``"linear"`` or            |
    |                |                           | ``"equal"``.               |
    +----------------+---------------------------+----------------------------+
    | ``cs``         | ``(mueff + 2) /           | Cumulation constant for    |
    |                | (N + mueff + 3)``         | step-size.                 |
    +----------------+---------------------------+----------------------------+
    | ``damps``      | ``1 + 2 * max(0, sqrt((   | Damping for step-size.     |
    |                | mueff - 1) / (N + 1)) - 1)|                            |
    |                | + cs``                    |                            |
    +----------------+---------------------------+----------------------------+
    | ``ccum``       | ``4 / (N + 4)``           | Cumulation constant for    |
    |                |                           | covariance matrix.         |
    +----------------+---------------------------+----------------------------+
    | ``ccov1``      | ``2 / ((N + 1.3)^2 +      | Learning rate for rank-one |
    |                | mueff)``                  | update.                    |
    +----------------+---------------------------+----------------------------+
    | ``ccovmu``     | ``2 * (mueff - 2 + 1 /    | Learning rate for rank-mu  |
    |                | mueff) / ((N + 2)^2 +     | update.                    |
    |                | mueff)``                  |                            |
    +----------------+---------------------------+----------------------------+
    """
    def __init__(self, population, sigma, params):
        self.centroid = copy.deepcopy(population[0])    # Create a centroid individual
        self.centroid[:] = self.centroid[0:0]           # Clear its content
        self.centroid.extend(numpy.mean(population, 0)) # The centroid is used in new individual creation
        
        self.dim = len(self.centroid)
        #self.centroid = numpy.array(self.centroid)
        self.sigma = sigma
        self.pc = numpy.zeros(self.dim)
        self.ps = numpy.zeros(self.dim)
        self.chiN = math.sqrt(self.dim) * (1 - 1. / (4. * self.dim) + \
                                      1. / (21. * self.dim**2))
        
        self.B = numpy.identity(self.dim)
        self.C = numpy.identity(self.dim)
        self.diagD = numpy.ones(self.dim)
        self.BD = self.B * self.diagD
        
        self.lambda_ = params.get("lambda_", int(4 + 3 * math.log(self.dim)))
        
        self.update_count = 0
        
        self.params = params
        self.compute_params(self.params)
        
    def generate(self):
        """Generate lambda offsprings from the current strategy using the 
        centroid individual as parent.
        """
        arz = numpy.random.randn(self.lambda_, self.dim)
        offsprings = list()
        empty_ind = copy.deepcopy(self.centroid)    # Create an individual
        empty_ind[:] = empty_ind[0:0]               # faster to copy
        for i in xrange(self.lambda_):
            ind = copy.deepcopy(empty_ind)
            #ind = copy.deepcopy(self.centroid)
            #ind[:] = ind[0:0]                       # Clear the new individual
            ind.extend(self.centroid + self.sigma * numpy.dot(self.BD, arz[i]))
            offsprings.append(ind)
        
        return offsprings
        
    def update(self, population):
        """Update the current Covariance Matrix Evolution Strategy.
        """
        sorted_pop = sorted(population, key=lambda ind: ind.fitness,
                            reverse=True)
        
        old_centroid = numpy.array(self.centroid)
        centroid = numpy.dot(self.weights, sorted_pop[0:self.mu])
        
        self.centroid[:] = self.centroid[0:0]      # Clear the centroid individual
        self.centroid.extend(centroid)
        
        c_diff = centroid - old_centroid
        
        # Cumulation : update evolution path
        self.ps = (1 - self.cs) * self.ps \
             + math.sqrt(self.cs * (2 - self.cs) * self.mueff) / self.sigma \
             * numpy.dot(self.B, (1. / self.diagD) \
                          * numpy.dot(self.B.T, c_diff))
        
        hsig = numpy.linalg.norm(self.ps) \
               / math.sqrt(1 - (1 - self.cs)**(2 * self.update_count)) \
               / self.chiN < 1.4 + 2 / (self.dim + 1)
               
        self.update_count += 1
               
        self.pc = (1 - self.cc) * self.pc \
             + hsig * (math.sqrt(self.cc * (2 - self.cc) * self.mueff) / \
                     self.sigma) * c_diff
        
        # Update covariance matrix
        artmp = sorted_pop[0:self.mu] - old_centroid
        self.C = (1 - self.ccov1 - self.ccovmu + (1 - hsig) \
                   * self.ccov1 * self.cc * (2 - self.cc)) * self.C \
                 + numpy.outer(self.ccov1 * self.pc, self.pc) \
                 + self.ccovmu \
                   * numpy.dot(artmp.T , (self.weights * artmp.T).T) \
                   / self.sigma**2
        
        self.sigma *= numpy.exp((numpy.linalg.norm(self.ps) / self.chiN - 1.) \
                                * self.cs / self.damps)
        
        self.diagD, self.B = numpy.linalg.eigh(self.C)
        indx = numpy.argsort(self.diagD)
        self.diagD = self.diagD[indx]
        self.diagD **= 0.5
        self.B = self.B[:,indx]
        self.BD = self.B * self.diagD

    def compute_params(self, params):
        """Those parameters depends on lambda and need to computed again if it 
        changes during evolution.
        """
        self.mu = params.get("mu", self.lambda_ / 2)
        rweights = params.get("weights", "superlinear")
        if rweights == "superlinear":
            self.weights = math.log(self.mu + 0.5) - \
                        numpy.log(numpy.arange(1, self.mu + 1))
        elif rweights == "linear":
            self.weights = mu + 0.5 - numpy.arange(1, self.mu + 1)
        elif rweights == "equal":
            self.weights = numpy.ones(self.mu)
        else:
            pass    # Print some warning ?
        
        self.weights /= sum(self.weights)
        self.mueff = 1. / sum(self.weights**2)
        
        self.cc = params.get("ccum", 4. / (self.dim + 4.))
        self.cs = params.get("cs", (self.mueff + 2.) / 
                                   (self.dim + self.mueff + 3.))
        self.ccov1 = params.get("ccov1", 2. / ((self.dim + 1.3)**2 + \
                                         self.mueff))
        self.ccovmu = params.get("ccovmu", 2. * (self.mueff - 2. +  \
                                                 1. / self.mueff) / \
                                           ((self.dim + 2.)**2 + self.mueff))
        self.ccovmu = min(1 - self.ccov1, self.ccovmu)
        self.damps = 1. + 2. * max(0, math.sqrt((self.mueff - 1.) / \
                                            (self.dim + 1.)) - 1.) + self.cs
        self.damps = params.get("damps", self.damps)
        

def rand(x):
    """Random test objective function."""
    return [numpy.random.random()]
    
def plane(x):
    """Plane test objective function."""
    return [x[0]]

def rastrigin(x):
    """Rastrigin test objective function. Consider using ``lambda_ = 20 * N`` 
    for this test function.
    """
    return [10 * len(x) + sum(map(lambda a: a**2 - 10 * math.cos(2 * math.pi * a), x))]
    #return 10 * len(x) + sum(x**2 - 10 * numpy.cos(2 * numpy.pi * x))
    
def sphere(x):
    """Sphere test objective function."""
    return [sum(map(lambda x: x**2, individual))]

def cigar(x):
    """Cigar test objective function."""
    return [x[0]**2 + 1e6 * sum(map(lambda a: a**2, x))]

def rosen(x):  
    """Rosenbrock test objective function."""
    return [sum(map(lambda x, y: 100 * (x**2 - y)**2 + (1. - x)**2, 
                   x[:-1], x[1:]))]
    