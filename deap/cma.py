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

#    Special thanks to Nikolaus Hansen for providing major part of 
#    this code. The CMA-ES algorithm is provided in many other languages
#    and advanced versions at http://www.lri.fr/~hansen/cmaesintro.html.

"""A module that provides support for the Covariance Matrix Adaptation 
Evolution Strategy.
"""

import logging
from math import sqrt, log, exp
import numpy
import random   # Only used to seed numpy.random
import sys      # Used to get maxint
import copy

numpy.random.seed(random.randint(0, sys.maxint))

_logger = logging.getLogger("deap.cma")
    
def esCMA(toolbox, population, ngen, halloffame=None, statistics=None):
    """The CMA-ES algorithm as described in Hansen, N. (2006). *The CMA
    Evolution Strategy: A Comparing Rewiew.*
    
    The provided *population* should be a list of one or more individuals.
    """
    _logger.info("Start of evolution")
        
    for g in xrange(ngen):
        _logger.info("Evolving generation %i", g)
        
        # Evaluate the individuals
        for ind in population:
            ind.fitness.values = toolbox.evaluate(ind)
        
        if halloffame is not None:
            halloffame.update(population)
        
        # Update the Strategy with the evaluated individuals
        toolbox.update(population)
        
        if statistics is not None:
            statistics.update(population)
            _logger.debug(statistics)

    _logger.info("End of (successful) evolution")

class CMAStrategy(object):
    """
    Additional configuration may be passed through the *params* argument as a 
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
    def __init__(self, centroid, sigma, **kargs):
        self.params = kargs
        
        # Create a centroid as a numpy array
        self.centroid = numpy.array(centroid)
        
        self.dim = len(self.centroid)
        self.sigma = sigma
        self.pc = numpy.zeros(self.dim)
        self.ps = numpy.zeros(self.dim)
        self.chiN = sqrt(self.dim) * (1 - 1. / (4. * self.dim) + \
                                      1. / (21. * self.dim**2))
        
        self.B = numpy.identity(self.dim)
        self.C = numpy.identity(self.dim)
        self.diagD = numpy.ones(self.dim)
        self.BD = self.B * self.diagD

        self.cond = 1       
 
        self.lambda_ = self.params.get("lambda_", int(4 + 3 * log(self.dim)))
        
        self.update_count = 0
        
        self.computeParams(self.params)
        
    def generate(self, ind_init):
        """Generate a population from the current strategy using the 
        centroid individual as parent.
        """
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.centroid + self.sigma * numpy.dot(arz, self.BD.T)
        return [ind_init(arzi) for arzi in arz]        
        
    def update(self, population):
        """Update the current covariance matrix strategy.
        """
        population.sort(key=lambda ind: ind.fitness, reverse=True)
        
        old_centroid = self.centroid
        self.centroid = numpy.dot(self.weights, population[0:self.mu])
        
        c_diff = self.centroid - old_centroid
        
        # Cumulation : update evolution path
        self.ps = (1 - self.cs) * self.ps \
             + sqrt(self.cs * (2 - self.cs) * self.mueff) / self.sigma \
             * numpy.dot(self.B, (1. / self.diagD) \
                          * numpy.dot(self.B.T, c_diff))
        
        hsig = float((numpy.linalg.norm(self.ps) / 
                sqrt(1. - (1. - self.cs)**(2. * (self.update_count + 1.))) / self.chiN
                < (1.4 + 2. / (self.dim + 1.))))

        self.update_count += 1
               
        self.pc = (1 - self.cc) * self.pc + hsig \
                  * sqrt(self.cc * (2 - self.cc) * self.mueff) / self.sigma \
                  * c_diff
                   
        # Update covariance matrix
        artmp = population[0:self.mu] - old_centroid
        self.C = (1 - self.ccov1 - self.ccovmu + (1 - hsig) \
                   * self.ccov1 * self.cc * (2 - self.cc)) * self.C \
                + self.ccov1 * numpy.outer(self.pc, self.pc) \
                + self.ccovmu * numpy.dot((self.weights * artmp.T), artmp) \
                / self.sigma**2
                
        
        self.sigma *= numpy.exp((numpy.linalg.norm(self.ps) / self.chiN - 1.) \
                                * self.cs / self.damps)
        
        self.diagD, self.B = numpy.linalg.eigh(self.C)
        indx = numpy.argsort(self.diagD)

        self.cond = self.diagD[indx[-1]]/self.diagD[indx[0]]

        self.diagD = self.diagD[indx]**0.5
        self.B = self.B[:, indx]
        self.BD = self.B * self.diagD
            
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.centroid + self.sigma * numpy.dot(arz, self.BD.T)
        for ind, arzi in zip(population, arz):
            del ind[:]
            ind.extend(arzi)

    def computeParams(self, params):
        """Those parameters depends on lambda and need to computed again if it 
        changes during evolution.
        """
        self.mu = params.get("mu", self.lambda_ / 2)
        rweights = params.get("weights", "superlinear")
        if rweights == "superlinear":
            self.weights = log(self.mu + 0.5) - \
                        numpy.log(numpy.arange(1, self.mu + 1))
        elif rweights == "linear":
            self.weights = self.mu + 0.5 - numpy.arange(1, self.mu + 1)
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
        self.damps = 1. + 2. * max(0, sqrt((self.mueff - 1.) / \
                                            (self.dim + 1.)) - 1.) + self.cs
        self.damps = params.get("damps", self.damps)
        
class CMA1pLStrategy(object):
    def __init__(self, parent, sigma, **kargs):
        self.parent = parent
        self.sigma = sigma
        self.dim = len(self.parent)

        self.C = numpy.identity(self.dim)
        self.A = numpy.identity(self.dim)
        
        self.pc = numpy.zeros(self.dim)
        
        self.computeParams(kargs)
        self.psucc = self.ptarg
        
    def computeParams(self, params):
        # Selection :
        self.lambda_ = params.get("lambda_", 1)
        
        # Step size control :
        self.d = params.get("d", 1.0 + self.dim/(2.0*self.lambda_))
        self.ptarg = params.get("ptarg", 1.0/(5+sqrt(self.lambda_)/2.0))
        self.cp = params.get("cp", self.ptarg*self.lambda_/(2+self.ptarg*self.lambda_))
        
        # Covariance matrix adaptation
        self.cc = params.get("cc", 2.0/(self.dim+2.0))
        self.ccov = params.get("ccov", 2.0/(self.dim**2 + 6.0))
        self.pthresh = params.get("pthresh", 0.44)
    
    def generate(self, ind_init):
        # self.y = numpy.dot(self.A, numpy.random.standard_normal(self.dim))
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.parent + self.sigma * numpy.dot(arz, self.A.T)        
        return [ind_init(arzi) for arzi in arz]
    
    def update(self, population):
        population.sort(key=lambda ind: ind.fitness, reverse=True)
        lambda_succ = sum(self.parent.fitness <= ind.fitness for ind in population)
        p_succ = float(lambda_succ) / self.lambda_
        self.psucc = (1-self.cp)*self.psucc + self.cp*p_succ
        
        if self.parent.fitness <= population[0].fitness:
            x_step = (population[0] - numpy.array(self.parent)) / self.sigma
            self.parent = copy.deepcopy(population[0])
            if self.psucc < self.pthresh:
                self.pc = (1 - self.cc)*self.pc + sqrt(self.cc * (2 - self.cc)) * x_step
                self.C = (1-self.ccov)*self.C + self.ccov * numpy.dot(self.pc, self.pc.T)
            else:
                self.pc = (1 - self.cc)*self.pc
                self.C = (1-self.ccov)*self.C + self.ccov * (numpy.dot(self.pc, self.pc.T) + self.cc*(2-self.cc)*self.C)

        self.sigma = self.sigma * exp(1.0/self.d * (self.psucc - self.ptarg)/(1.0-self.ptarg))
        
        # We use Cholesky since for now we have no use of eigen decomposition
        # Basically, Cholesky returns a matrix A as C = A*A.T
        # Eigen decomposition returns two matrix B and D^2 as C = B*D^2*B.T = B*D*D*B.T
        # So A == B*D
        # To compute the new individual we need to multiply each vector z by A
        # as y = centroid + sigma * A*z
        # So the Cholesky is more straightforward as we don't need to compute 
        # the squareroot of D^2, and multiply B and D in order to get A, we directly get A.
        # This can't be done (without cost) with the standard CMA-ES as the eigen decomposition is used
        # to compute covariance matrix inverse in the step-size evolutionary path computation.
        self.A = numpy.linalg.cholesky(self.C)
        
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.parent + self.sigma * numpy.dot(arz, self.A.T)
        for ind, arzi in zip(population, arz):
            del ind[:]
            ind.extend(arzi)
        
