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
import numpy
import copy
from math import sqrt, log, exp

import tools

class Strategy(object):
    """
    A strategy that will keep track of the basic parameters of the CMA-ES
    algorithm.
    
    :param centroid: An iterable object that indicates where to start the
                     evolution.
    :param sigma: The initial standard deviation of the distribution.
    :param parameter: One or more parameter to pass to the strategy as
                      described in the following table, optional.
    
    +----------------+---------------------------+----------------------------+
    | Parameter      | Default                   | Details                    |
    +================+===========================+============================+
    | ``lambda_``    | ``int(4 + 3 * log(N))``   | Number of children to      |
    |                |                           | produce at each generation,|
    |                |                           | ``N`` is the individual's  |
    |                |                           | size (integer).            |
    +----------------+---------------------------+----------------------------+
    | ``mu``         | ``int(lambda_ / 2)``      | The number of parents to   | 
    |                |                           | keep from the              |
    |                |                           | lambda children (integer). |
    +----------------+---------------------------+----------------------------+
    | ``cmatrix``    | ``identity(N)``           | The initial covariance     |
    |                |                           | matrix of the distribution |
    |                |                           | that will be sampled.      |
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
        
        self.C = self.params.get("cmatrix", numpy.identity(self.dim))
        self.diagD, self.B = numpy.linalg.eigh(self.C)

        indx = numpy.argsort(self.diagD)
        self.diagD = self.diagD[indx]**0.5
        self.B = self.B[:, indx]
        self.BD = self.B * self.diagD
        
        self.cond = self.diagD[indx[-1]]/self.diagD[indx[0]]
        
        self.lambda_ = self.params.get("lambda_", int(4 + 3 * log(self.dim)))
        self.update_count = 0
        self.computeParams(self.params)
        
    def generate(self, ind_init):
        """Generate a population of :math:`\lambda` individuals of type
        *ind_init* from the current strategy.
        
        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: A list of individuals.
        """
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.centroid + self.sigma * numpy.dot(arz, self.BD.T)
        return map(ind_init, arz)
        
    def update(self, population):
        """Update the current covariance matrix strategy from the
        *population*.
        
        :param population: A list of individuals from which to update the
                           parameters.
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

    def computeParams(self, params):
        """Computes the parameters depending on :math:`\lambda`. It needs to
        be called again if :math:`\lambda` changes during evolution.
        
        :param params: A dictionary of the manually set parameters.
        """
        self.mu = params.get("mu", int(self.lambda_ / 2))
        rweights = params.get("weights", "superlinear")
        if rweights == "superlinear":
            self.weights = log(self.mu + 0.5) - \
                        numpy.log(numpy.arange(1, self.mu + 1))
        elif rweights == "linear":
            self.weights = self.mu + 0.5 - numpy.arange(1, self.mu + 1)
        elif rweights == "equal":
            self.weights = numpy.ones(self.mu)
        else:
            raise RuntimeError("Unknown weights : %s" % rweights)
        
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
        
class StrategyOnePlusLambda(object):
    """
    A CMA-ES strategy that uses the :math:`1 + \lambda` paradigme.
    
    :param parent: An iterable object that indicates where to start the
                   evolution. The parent requires a fitness attribute.
    :param sigma: The initial standard deviation of the distribution.
    :param parameter: One or more parameter to pass to the strategy as
                      described in the following table, optional.
    """
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
        """Computes the parameters depending on :math:`\lambda`. It needs to
        be called again if :math:`\lambda` changes during evolution.
        
        :param params: A dictionary of the manually set parameters.
        """
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
        """Generate a population of :math:`\lambda` individuals of type
        *ind_init* from the current strategy.
        
        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: A list of individuals.
        """
        # self.y = numpy.dot(self.A, numpy.random.standard_normal(self.dim))
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.parent + self.sigma * numpy.dot(arz, self.A.T)        
        return map(ind_init, arz)
    
    def update(self, population):
        """Update the current covariance matrix strategy from the
        *population*.
        
        :param population: A list of individuals from which to update the
                           parameters.
        """
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
        
class StrategyMultiObjective(object):
    def __init__(self, population, sigma, **params):
        self.parents = population
        self.dim = len(self.parents[0])

        self.sigmas = [sigma] * len(population)
        self.C = [numpy.identity(self.dim) for _ in range(len(population))]
        self.A = [numpy.identity(self.dim) for _ in range(len(population))]
        
        self.pc = [numpy.zeros(self.dim) for _ in range(len(population))]
        self.computeParams(params)
        self.psucc = [self.ptarg] * len(population)

        self.success_count = 0

    def computeParams(self, params):
        """Computes the parameters depending on :math:`\lambda`. It needs to
        be called again if :math:`\lambda` changes during evolution.
        
        :param params: A dictionary of the manually set parameters.
        """
        # Selection :
        self.lambda_ = params.get("lambda_", 1)
        self.mu = params.get("mu", len(self.parents))
        
        # Step size control :
        self.d = params.get("d", 1.0 + self.dim / 2.0)
        self.ptarg = params.get("ptarg", 1.0 / (5.0 + 0.5))
        self.cp = params.get("cp", self.ptarg / (2.0 + self.ptarg))
        
        # Covariance matrix adaptation
        self.cc = params.get("cc", 2.0 / (self.dim + 2.0))
        self.ccov = params.get("ccov", 2.0 / (self.dim**2 + 6.0))
        self.pthresh = params.get("pthresh", 0.44)

    def generate(self, ind_init):
        for i, p in enumerate(self.parents):
            p._ps = "p", i

        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        individuals = list()
        if self.lambda_ == self.mu:
            for i in range(self.lambda_):
                individuals.append(ind_init(self.parents[i] + self.sigmas[i] * numpy.dot(arz[i], self.A[i])))
                individuals[-1]._ps = "o", i
        else:
            ndom = tools.sortLogNondominated(self.parents, len(self.parents), first_front_only=True)
            for i in range(self.lambda_):
                j = numpy.random.randint(0, len(ndom))
                _, p_idx = ndom[j]._ps
                individuals.append(ind_init(self.parents[p_idx] + self.sigmas[p_idx] * numpy.dot(arz[i], self.A[p_idx].T)))
                individuals[-1]._ps = "o", p_idx
        
        

        return individuals

    def update(self, population):
        candidates = population + self.parents
        # print len(candidates)
        
        if len(candidates) <= self.mu:
            chosen = candidates
        else:
            # print candidates
            pareto_fronts = tools.sortLogNondominated(candidates, len(candidates))

            chosen = list()
            mid_front = None
            not_chosen = list()

            # print "Num Fronts", len(pareto_fronts)

            # Fill the next population (chosen) witht the fronts until there is not enouch space
            # When an entire front does not fit in the space left we rely on the hypervolume
            # for this front
            # The remaining fronts are explicitely not chosen
            full = False
            for i, front in enumerate(pareto_fronts):
                # print len(front)
                if len(chosen) + len(front) <= self.mu and not full:
                    # print "chosen"
                    chosen += front
                elif mid_front is None and len(chosen) < self.mu:
                    # print "mid_front"
                    # print len(front)
                    mid_front = front
                else:
                    # print "not chosen"
                    not_chosen += front
                    full = True

            # Separate the mid front to accept only k individuals
            k = self.mu - len(chosen)
            if k > 0:
                # reference point is chosen in the complete population
                # as the worst in each dimension +1
                ref = numpy.array([ind.fitness.wvalues for ind in candidates]) * -1
                ref = numpy.max(ref, axis=0) + 1
                keep_idx = tools.hypervolume_kmax(mid_front, k, ref)
                rm_idx = set(range(len(mid_front))) - set(keep_idx)
                chosen += [mid_front[i] for i in keep_idx]
                not_chosen += [mid_front[i] for i in rm_idx]

        print(len(chosen))

        cp, cc, ccov = self.cp, self.cc, self.ccov
        d, ptarg, pthresh = self.d, self.ptarg, self.pthresh

        # Make copies for chosen offsprings only
        last_steps = [self.sigmas[ind._ps[1]] if ind._ps[0] == "o" else None for ind in chosen]
        sigmas = [self.sigmas[ind._ps[1]] if ind._ps[0] == "o" else None for ind in chosen]
        C = [self.C[ind._ps[1]].copy() if ind._ps[0] == "o" else None for ind in chosen]
        pc = [self.pc[ind._ps[1]].copy() if ind._ps[0] == "o" else None for ind in chosen]
        psucc = [self.psucc[ind._ps[1]] if ind._ps[0] == "o" else None for ind in chosen]

        step_size = 0

        # Update the appropriate internal parameters
        for i, ind in enumerate(chosen):
            t, p_idx = ind._ps
            
            # Only the offsprings update the parameter set
            if t == "o":
                step_size += sigmas[i]
                self.success_count += 1

                # Update (Success = 1 since it is chosen)
                psucc[i] = (1.0 - cp) * psucc[i] + cp
                sigmas[i] = sigmas[i] * exp((psucc[i] - ptarg) / (d * (1.0 - ptarg)))

                if psucc[i] < pthresh:
                    xp = numpy.array(ind)
                    x = numpy.array(self.parents[p_idx])
                    # print(self.parents[p_idx]._ps, ind._ps)
                    pc[i] = (1.0 - cc) * pc[i] + sqrt(cc * (2.0 - cc)) * (xp - x) / last_steps[i]
                    C[i] = (1.0 - ccov) * C[i] + ccov * numpy.outer(pc[i], pc[i])
                else:
                    pc[i] = (1.0 - cc) * pc[i]
                    C[i] = (1.0 - ccov) * C[i] + ccov * (numpy.outer(pc[i], pc[i]) + cc * (2.0 - cc) * C[i])

                self.psucc[p_idx] = (1.0 - cp) * self.psucc[p_idx] + cp
                self.sigmas[p_idx] = self.sigmas[p_idx] * exp((self.psucc[p_idx] - ptarg) / (d * (1.0 - ptarg)))


        # It is unnecessary to update the entire parameter set for not chosen individuals
        # These parameters will not make it to the next generation
        for ind in not_chosen:
            t, p_idx = ind._ps
            
            # Only the offsprings update the parameter set
            if t == "o":
                step_size += self.sigmas[p_idx]
                self.psucc[p_idx] = (1.0 - cp) * self.psucc[p_idx]
                self.sigmas[p_idx] = self.sigmas[p_idx] * exp((self.psucc[p_idx] - ptarg) / (d * (1.0 - ptarg)))
        
        print "Step size", step_size / self.lambda_

        # Make a copy of the internal parameters
        # The parameter is in the temporary variable for offspring and in the original one for parents
        self.parents = chosen
        self.sigmas = [sigmas[i] if ind._ps[0] == "o" else self.sigmas[ind._ps[1]] for i, ind in enumerate(chosen)]
        self.C = [C[i] if ind._ps[0] == "o" else self.C[ind._ps[1]] for i, ind in enumerate(chosen)]
        self.pc = [pc[i] if ind._ps[0] == "o" else self.pc[ind._ps[1]] for i, ind in enumerate(chosen)]
        self.psucc = [psucc[i] if ind._ps[0] == "o" else self.psucc[ind._ps[1]] for i, ind in enumerate(chosen)]

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
        self.A = [numpy.linalg.cholesky(self.C[i]) if ind._ps[0] == "o" else self.A[ind._ps[1]] for i, ind in enumerate(chosen)]