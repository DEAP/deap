
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
import math
import random

try:
    import numpy
except:
    raise ImportError, "NumPy is required by the CMA-ES package, you can find NumPy at http://numpy.scipy.org/"
    
def cmaes(individual, sigma, **kargs):
    indsize = len(individual)
    fitness_model = copy.deepcopy(individual.fitness)
    
    dict = kargs
    
    lambda_ = dict.get("lambda_", int(4 + 3 * math.log(indsize)))
    lambda_last = lambda_
    
    xmean = individual[:]
    ########### TEMP
    #sigma = numpy.ones(indsize)
    ########### TEMP
    
    pc = numpy.zeros(indsize)
    ps = numpy.zeros(indsize)
    chiN = math.sqrt(indsize) * (1 - 1. / (4. * indsize) + 1. / (21. * indsize**2))
    
    B = numpy.identity(indsize)
    C = numpy.identity(indsize)
    diagD = numpy.ones(indsize)
    BD = B * diagD
    
    itercount = 0
    evalcount = 0
    stop_flags = []
    
    while True not in stop_flags:
        # Initialization of the parameters at first iteration or when 
        # the population size change
        if itercount == 0 or lambda_ != lambda_last:
            lambda_last = lambda_
            mu = dict.get("mu", lambda_ / 2)
            rweights = dict.get("recombination_weights", "superlinear")
            if rweights == "superlinear":
                weights = math.log(mu + 0.5) - numpy.log(numpy.arange(1, mu + 1))
            elif rweights == "linear":
                weights = mu + 0.5 - numpy.arange(1, mu + 1)
            elif rweights == "equal":
                weights = numpy.ones(mu)
            else:
                pass    # Print some warning ?
            
            mueff = sum(weights)**2 / sum(weights**2)
            weights /= sum(weights)
            
            cc = dict.get("ccum", 4. / (indsize + 4.))
            cs = dict.get("cs", (mueff + 2.) / (indsize + mueff + 3.))
            
            ccov1 = dict.get("ccov1", 2. / ((indsize + 1.3)**2 + mueff))
            ccovmu = min(1 - ccov1, dict.get("ccovmu", 2. * (mueff - 2. + 1. / mueff) / ((indsize + 2.)**2 + mueff)))
            
            damps = dict.get("damps", 1. + 2. * max(0, math.sqrt((mueff - 1.) / (indsize + 1.)) -1.) + cs)
        
        itercount += 1
        
        # Handle boundaries ?
        
        # Generate lambda offsprings
        arz = numpy.random.randn(lambda_, indsize)
        arx = numpy.empty((lambda_, indsize), dtype=arz.dtype)
        for i in xrange(lambda_):
            arx[i] = xmean + sigma * numpy.dot(BD, arz[i])
        
        # Evaluation ... Test with rastrigin
        fitnesses = numpy.empty((lambda_,))
        for i in xrange(lambda_):
            fitnesses[i] = rosen(arx[i])
        
        sorted_indx = numpy.argsort(fitnesses)
        print fitnesses[sorted_indx[0]]
        
        xold = numpy.array(xmean)
        xmean = numpy.sum(weights * arx[sorted_indx[0:mu]].T, 1)
        zmean = numpy.sum(weights * arz[sorted_indx[0:mu]].T, 1)
        
        ps = (1 - cs) * ps + math.sqrt(cs * (2 - cs) * mueff) * (B * zmean)
        hsig = numpy.linalg.norm(ps) / math.sqrt(1 - (1 - cs)**(2 * itercount)) / chiN < 1.4 + 2/(indsize + 1)
        
        pc = (1 - cc) * pc + hsig * (math.sqrt(cc * (2 - cc) * mueff) / sigma) * (xmean - xold)
        
        #Z = numpy.zeros((indsize,indsize))
        #for i in xrange(mu): 
        #    z = arx[sorted_indx[i]] - xold 
        #    Z += numpy.outer((ccovmu * weights[i] / sigma**2) * z, z)
        #C = (1 - ccov1 - ccovmu) * C + numpy.outer(ccov1 * pc, pc) + Z
        
        #artmp = arx[sorted_indx[0:mu]] - xold
        #C = (1 - ccov1 - ccovmu + (1 - hsig) * ccov1 * cc * (2 - cc)) * C \
        #    + ccov1 * pc.T * pc \
        #    + numpy.dot((ccovmu * weights) * artmp.T , artmp) / (sigma**2)
        
        C = (1 - ccov1) * C + ccov1 * pc * pc.T
            
        sigma = sigma * numpy.exp((numpy.linalg.norm(ps) / chiN - 1) * cs / damps)
        
        diagD, B = numpy.linalg.eigh(C)
        sorted_indx = numpy.argsort(diagD)
        diagD = diagD[sorted_indx]
        B = B[:,sorted_indx]
        BD = B * diagD
        
        if fitnesses[sorted_indx[0]] < 1*10**-7:
            stop_flags.append(True)
        

def configure(indsize, dict):
    """This function configure the CMA-ES algorithm by initializing external
    parameters with default values or input parameters provided in *dict*.
    It returns a :class:`StrategyParameters` object containing all
    required parameters.
    
    +----------------------------+---------------------------+---------------------------------------------+
    | Parameter                  | Default                   | Details                                     |
    +============================+===========================+=============================================+
    | ``"lambda"``               | ``floor(4 + 3 * log(N))`` | Number of childrens to produce at each      |
    |                            |                           | generation, ``N`` is the individual's size. |
    +----------------------------+---------------------------+---------------------------------------------+
    | ``"mu"``                   | ``floor(lambda / 2)``     | The number of parents to keep from the      |
    |                            |                           | lambda childrens.                           |
    +----------------------------+---------------------------+---------------------------------------------+
    | ``"recombination_weights"``| ``"superlinear"``         | Decrease speed, can be ``"superlinear"``,   |
    |                            |                           | ``"linear"`` or ``"equal"``.                |
    +----------------------------+---------------------------+---------------------------------------------+
    | ``"cs"``                   | ``(mueff + 2) /           | Cumulation constant for step-size.          |
    |                            | (N + mueff + 3)``         |                                             |
    +----------------------------+---------------------------+---------------------------------------------+
    | ``"damps"``                | ``1 + 2 * max(0, sqrt((   | Damping for step-size.                      |
    |                            | mueff - 1) / (N + 1)) - 1)|                                             |
    |                            | + cs``                    |                                             |
    +----------------------------+---------------------------+---------------------------------------------+
    | ``"ccum"``                 | ``4 / (N + 4)``           | Cumulation constant for covariance matrix.  |
    +----------------------------+---------------------------+---------------------------------------------+
    | ``"ccov1"``                | ``2 / ((N + 1.3)^2 +      | Learning rate for rank-one update.          |
    |                            | mueff)``                  |                                             |
    +----------------------------+---------------------------+---------------------------------------------+
    | ``"ccovmu"``               | ``2 * (mueff - 2 + 1 /    | Learning rate for rank-mu update.           |
    |                            | mueff) / ((N + 2)^2 +     |                                             |
    |                            | mueff)``                  |                                             |
    +----------------------------+---------------------------+---------------------------------------------+
    """
    params = type("StrategyParameters", (object,), {})
    
    if dict is not None:
        params.lambda_ = dict.pop("lambda", None)   # int(4 + 3 * log(indsize))
        params.mu = dict.pop("mu", None)            # int(params.lambda_ / 2)
        params.recombination_weights = dict.pop("recombination_weights", None) # "superlinear"
        # Missing Diagonal Only, really usefull ?
        
        params.cs = dict.pop("cs", None)            # (mueff + 2.) / ( N + mueff + 3.)
        params.damps = dict.pop("damps", None)      # 1. + 2. * max(0, sqrt((mueff - 1.) / (N + 1.)) -1.) + cs
        params.ccum = dict.pop("ccum", None)        # 4. / (indsize + 4.)
        params.ccov1 = dict.pop("ccov1", None)      # 2. / ((N + 1.3)^2 + mueff)
        params.ccovmu = dict.pop("ccovmu", None)    # 2. * (mueff - 2. + 1. / mueff) / ((N + 2.)^2 + mueff)
    
        if len(dict) > 0:
            pass    # Print some warning ?
            
    return params
    
    
class CMAStrategy(object):
    def __init__(self, individual, sigma, lambda_):
        ind_len = len(individual)
        self.mean = numpy.array(individual)
        self.sigma = sigma
        self.update_params(lambda_, ind_len)
        # TODO : add code for an initialized C matrix
        self.B = numpy.identity(ind_len)
        self.C = numpy.identity(ind_len)
        self.dC = numpy.ones(ind_len)           # Diagonal elements of matrix C
        self.D = numpy.ones(ind_len)            # Diagonal Matrix
        self.BD = self.B * self.D               # For optimization of mutation
        self.pc = numpy.zeros(ind_len)
        self.ps = numpy.zeros(ind_len)
        self.chi = math.sqrt(ind_len) * (1 - 1. / (4. * ind_len) + 1. / (21. * ind_len**2))
        
    def update(self, individuals):
        # Sort the individuals so the better one comes first
        sorted_inds = sorted(individuals, key=lambda ind : ind.fitness, reverse=True)
        
        # Compute new mean
        old_mean = self.mean
        self.mean = numpy.sum(self.weights * numpy.array(sorted_inds[0:self.mu]).T, 1)
        
        # Adapt covariance matrix
        self.pc = (1 - self.cc) * self.pc + \
                  math.sqrt(self.cc * (2 - self.cc) * self.mueff) \
                  * (self.mean - old_mean) / self.sigma
        self.C = (1 - self.ccov) * self.C + self.ccov * self.pc * self.pc.T
        
        # Adapt step size
        self.ps = (1 - self.cs) * self.ps + \
                  (math.sqrt(self.cs * (2 - self.cs) * self.mueff)  / self.sigma) \
                  * numpy.dot(self.B, (1./self.D) * numpy.dot(self.B.T, (self.mean - old_mean)))
        self.sigma *= numpy.exp(min(1, (self.cs / self.damps) *
                                (math.sqrt(sum(self.ps**2)) / self.chi - 1)))
        
        # Update B and D from C
        self.D, self.B = numpy.linalg.eigh(self.C)
        indexes = numpy.argsort(self.D)
        self.D = self.D[indexes]
        self.B = self.B[:,indexes]
        self.BD = self.B * self.D
    
    def update_params(self, popsize, ind_len):
        # TODO : add code for non-default parameters
        self.lambda_ = popsize
        self.mu = popsize / 2                   # popsize / 2. rounded down (int(2) is intended).
        self.weights = math.log(self.mu + 0.5) - numpy.log(1. + numpy.arange(self.mu))
        self.weights /= sum(self.weights)
        self.mueff = 1. / sum(self.weights**2)
        self.cc = 4. / (ind_len + 4.)
        self.cs = (self.mueff + 2) / (ind_len + self.mueff + 3)
        self.ccov = 2. / math.sqrt(ind_len + math.sqrt(2.))
        self.damps = 1. / self.cs + 1
        self.cw = sum(self.weights) / math.sqrt(sum(self.weights**2))
        
def rastrigin(x):
    """Rastrigin test objective function"""
    N = len(x)
    return 10 * N + sum(x**2 - 10 * numpy.cos(2 * numpy.pi * x))
    
def sphere(x):
    return sum(x**2)

def cigar(x, rot=0):
    """Cigar test objective function"""
    #if rot:
    #    x = rotate(x)  
    return x[0]**2 + 1e6 * sum(x[1:]**2)

def rosen(x):  
    """Rosenbrock test objective function"""
    return sum(100.*(x[:-1]**2-x[1:])**2 + (1.-x[:-1])**2)
    