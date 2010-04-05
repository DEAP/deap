
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
    
def cmaes(toolbox, individual, sigma, **kargs):
    """The CMA-Es algorithm as described in ...
    
    Additional configuration may be passed throught the keyworded arguments,
    
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
    indsize = len(individual)
    
    dict = kargs
    
    lambda_ = dict.get("lambda_", int(4 + 3 * math.log(indsize)))
    lambda_last = lambda_
    
    xmean = individual[:]
    ########### TEMP
    #sigma = numpy.ones(indsize) * sigma
    ########### TEMP
    
    pc = numpy.zeros(indsize)
    ps = numpy.zeros(indsize)
    chiN = math.sqrt(indsize) * (1 - 1. / (4. * indsize) + \
                                     1. / (21. * indsize**2))
    
    B = numpy.identity(indsize)
    C = numpy.identity(indsize)
    diagD = numpy.ones(indsize)
    BD = B * diagD
    
    itercount = 0
    evalcount = 0
    stop_flags = []
    
    S = []
    
    while True not in stop_flags:
        # Initialization of the parameters at first iteration or when 
        # the population size change
        if itercount == 0 or lambda_ != lambda_last:
            lambda_last = lambda_
            mu = dict.get("mu", lambda_ / 2)
            rweights = dict.get("weights", "superlinear")
            if rweights == "superlinear":
                weights = math.log(mu + 0.5) - \
                          numpy.log(numpy.arange(1, mu + 1))
            elif rweights == "linear":
                weights = mu + 0.5 - numpy.arange(1, mu + 1)
            elif rweights == "equal":
                weights = numpy.ones(mu)
            else:
                pass    # Print some warning ?
            
            weights /= sum(weights)
            mueff = 1. / sum(weights**2)
            
            cc = dict.get("ccum", 4. / (indsize + 4.))
            cs = dict.get("cs", (mueff + 2.) / (indsize + mueff + 3.))
            
            
            ccov1 = dict.get("ccov1", 2. / ((indsize + 1.3)**2 + mueff))
            ccovmu = dict.get("ccovmu", 2. * (mueff - 2. + 1. / mueff) / \
                                             ((indsize + 2.)**2 + mueff))
            ccovmu = min(1 - ccov1, ccovmu)
            
            damps = 1. + 2. * max(0, math.sqrt((mueff - 1.) / \
                                               (indsize + 1.)) - 1.) + cs
            damps = dict.get("damps", damps)
        
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
            fitnesses[i] = toolbox.evaluate(arx[i])
        
        sorted_indx = numpy.argsort(fitnesses)
        print fitnesses[sorted_indx[0]]
        
        xold = numpy.array(xmean)
        xmean = numpy.dot(weights, arx[sorted_indx[0:mu]])
        zmean = numpy.dot(weights, arz[sorted_indx[0:mu]])
        
        # Cumulation : update evolution path
        ps = (1 - cs) * ps + \
             math.sqrt(cs * (2 - cs) * mueff) * numpy.dot(B.T, zmean)
        
        hsig = numpy.linalg.norm(ps) / \
               math.sqrt(1 - (1 - cs)**(2 * itercount)) / \
               chiN < 1.4 + 2/(indsize + 1)
        
        pc = (1 - cc) * pc + \
             hsig * (math.sqrt(cc * (2 - cc) * mueff) / sigma) * (xmean - xold)
        
        
        #Z = numpy.zeros((indsize,indsize))
        #for i in xrange(mu): 
        #    z = arx[sorted_indx[i]] - xold 
        #    Z += numpy.outer((ccovmu * weights[i] / sigma**2) * z, z)
        #C = (1 - ccov1 - ccovmu) * C + numpy.outer(ccov1 * pc, pc) + Z
        
        # Covariance matrix update
        artmp = arx[sorted_indx[0:mu]] - xold
        C = (1 - ccov1 - ccovmu + (1 - hsig) * ccov1 * cc * (2 - cc)) * C \
            + numpy.outer(ccov1 * pc, pc) \
            + ccovmu * numpy.dot(artmp.T , (weights * artmp.T).T) / sigma**2
        
        #C = (1 - ccov1) * C + ccov1 * pc * pc
        
        sigma *= numpy.exp((numpy.linalg.norm(ps) / chiN - 1.) * cs / damps)
        
        diagD, B = numpy.linalg.eigh(C)
        indx = numpy.argsort(diagD)
        diagD = diagD[indx]
        diagD **= 0.5
        B = B[:,indx]
        BD = B * diagD
        
        if fitnesses[sorted_indx[0]] < 10**-7:
            stop_flags.append(True)
            
    for i, attr in enumerate(arx[sorted_indx[0]]):
        individual[i] = attr
    individual.fitness.append(fitnesses[sorted_indx[0]])
    return individual


def rand(x):
    """Random test objective function."""
    return numpy.random.random()
    
def plane(x):
    """Plane test objective function."""
    return x[0]

def rastrigin(x):
    """Rastrigin test objective function. Consider using ``lambda_ = 20 * N`` 
    for this test function.
    """
    return 10 * len(x) + sum(x**2 - 10 * numpy.cos(2 * numpy.pi * x))
    
def sphere(x):
    """Sphere test objective function."""
    return sum(x**2)

def cigar(x, rot=0):
    """Cigar test objective function."""
    #if rot:
    #    x = rotate(x)  
    return x[0]**2 + 1e6 * sum(x[1:]**2)

def rosen(x):  
    """Rosenbrock test objective function."""
    return sum(100.*(x[:-1]**2-x[1:])**2 + (1.-x[:-1])**2)
    