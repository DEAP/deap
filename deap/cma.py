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
import copy
from math import sqrt, log, exp
from itertools import cycle
import warnings

import numpy

from . import tools


class Strategy(object):
    """
    A strategy that will keep track of the basic parameters of the CMA-ES
    algorithm ([Hansen2001]_).

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

    .. [Hansen2001] Hansen and Ostermeier, 2001. Completely Derandomized
       Self-Adaptation in Evolution Strategies. *Evolutionary Computation*

    """
    def __init__(self, centroid, sigma, **kargs):
        self.params = kargs

        # Create a centroid as a numpy array
        self.centroid = numpy.array(centroid)

        self.dim = len(self.centroid)
        self.sigma = sigma
        self.pc = numpy.zeros(self.dim)
        self.ps = numpy.zeros(self.dim)
        self.chiN = sqrt(self.dim) * (1 - 1. / (4. * self.dim)
                                      + 1. / (21. * self.dim ** 2))

        self.C = self.params.get("cmatrix", numpy.identity(self.dim))
        self.diagD, self.B = numpy.linalg.eigh(self.C)

        indx = numpy.argsort(self.diagD)
        self.diagD = self.diagD[indx] ** 0.5
        self.B = self.B[:, indx]
        self.BD = self.B * self.diagD

        self.cond = self.diagD[indx[-1]] / self.diagD[indx[0]]

        self.lambda_ = self.params.get("lambda_", int(4 + 3 * log(self.dim)))
        self.update_count = 0
        self.computeParams(self.params)

    def generate(self, ind_init):
        r"""Generate a population of :math:`\lambda` individuals of type
        *ind_init* from the current strategy.

        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: A list of individuals.
        """
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.centroid + self.sigma * numpy.dot(arz, self.BD.T)
        return [ind_init(a) for a in arz]

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
            * numpy.dot(self.B, (1. / self.diagD)
                        * numpy.dot(self.B.T, c_diff))

        hsig = float((numpy.linalg.norm(self.ps)
                      / sqrt(1. - (1. - self.cs) ** (2. * (self.update_count + 1.))) / self.chiN
                      < (1.4 + 2. / (self.dim + 1.))))

        self.update_count += 1

        self.pc = (1 - self.cc) * self.pc + hsig \
            * sqrt(self.cc * (2 - self.cc) * self.mueff) / self.sigma \
            * c_diff

        # Update covariance matrix
        artmp = population[0:self.mu] - old_centroid
        self.C = (1 - self.ccov1 - self.ccovmu + (1 - hsig)
                  * self.ccov1 * self.cc * (2 - self.cc)) * self.C \
            + self.ccov1 * numpy.outer(self.pc, self.pc) \
            + self.ccovmu * numpy.dot((self.weights * artmp.T), artmp) \
            / self.sigma ** 2

        self.sigma *= numpy.exp((numpy.linalg.norm(self.ps) / self.chiN - 1.)
                                * self.cs / self.damps)

        self.diagD, self.B = numpy.linalg.eigh(self.C)
        indx = numpy.argsort(self.diagD)

        self.cond = self.diagD[indx[-1]] / self.diagD[indx[0]]

        self.diagD = self.diagD[indx] ** 0.5
        self.B = self.B[:, indx]
        self.BD = self.B * self.diagD

    def computeParams(self, params):
        r"""Computes the parameters depending on :math:`\lambda`. It needs to
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
        self.mueff = 1. / sum(self.weights ** 2)

        self.cc = params.get("ccum", 4. / (self.dim + 4.))
        self.cs = params.get("cs", (self.mueff + 2.)
                             / (self.dim + self.mueff + 3.))
        self.ccov1 = params.get("ccov1", 2. / ((self.dim + 1.3) ** 2
                                               + self.mueff))
        self.ccovmu = params.get("ccovmu", 2. * (self.mueff - 2.
                                                 + 1. / self.mueff)
                                 / ((self.dim + 2.) ** 2 + self.mueff))
        self.ccovmu = min(1 - self.ccov1, self.ccovmu)
        self.damps = 1. + 2. * max(0, sqrt((self.mueff - 1.)
                                           / (self.dim + 1.)) - 1.) + self.cs
        self.damps = params.get("damps", self.damps)


class StrategyOnePlusLambda(object):
    r"""
    A CMA-ES strategy that uses the :math:`1 + \lambda` paradigm ([Igel2007]_).

    :param parent: An iterable object that indicates where to start the
                   evolution. The parent requires a fitness attribute.
    :param sigma: The initial standard deviation of the distribution.
    :param lambda_: Number of offspring to produce from the parent.
                    (optional, defaults to 1)
    :param parameter: One or more parameter to pass to the strategy as
                      described in the following table. (optional)

    Other parameters can be provided as described in the next table

    +----------------+---------------------------+----------------------------+
    | Parameter      | Default                   | Details                    |
    +================+===========================+============================+
    | ``d``          | ``1.0 + N / (2.0 *        | Damping for step-size.     |
    |                | lambda_)``                |                            |
    +----------------+---------------------------+----------------------------+
    | ``ptarg``      | ``1.0 / (5 + sqrt(lambda_)| Target success rate.       |
    |                | / 2.0)``                  |                            |
    +----------------+---------------------------+----------------------------+
    | ``cp``         | ``ptarg * lambda_ / (2.0 +| Step size learning rate.   |
    |                | ptarg * lambda_)``        |                            |
    +----------------+---------------------------+----------------------------+
    | ``cc``         | ``2.0 / (N + 2.0)``       | Cumulation time horizon.   |
    +----------------+---------------------------+----------------------------+
    | ``ccov``       | ``2.0 / (N**2 + 6.0)``    | Covariance matrix learning |
    |                |                           | rate.                      |
    +----------------+---------------------------+----------------------------+
    | ``pthresh``    | ``0.44``                  | Threshold success rate.    |
    +----------------+---------------------------+----------------------------+

    .. [Igel2007] Igel, Hansen, Roth, 2007. Covariance matrix adaptation for
       multi-objective optimization. *Evolutionary Computation* Spring;15(1):1-28

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
        r"""Computes the parameters depending on :math:`\lambda`. It needs to
        be called again if :math:`\lambda` changes during evolution.

        :param params: A dictionary of the manually set parameters.
        """
        # Selection :
        self.lambda_ = params.get("lambda_", 1)

        # Step size control :
        self.d = params.get("d", 1.0 + self.dim / (2.0 * self.lambda_))
        self.ptarg = params.get("ptarg", 1.0 / (5 + sqrt(self.lambda_) / 2.0))
        self.cp = params.get("cp", self.ptarg * self.lambda_ / (2 + self.ptarg * self.lambda_))

        # Covariance matrix adaptation
        self.cc = params.get("cc", 2.0 / (self.dim + 2.0))
        self.ccov = params.get("ccov", 2.0 / (self.dim ** 2 + 6.0))
        self.pthresh = params.get("pthresh", 0.44)

    def generate(self, ind_init):
        r"""Generate a population of :math:`\lambda` individuals of type
        *ind_init* from the current strategy.

        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: A list of individuals.
        """
        # self.y = numpy.dot(self.A, numpy.random.standard_normal(self.dim))
        arz = numpy.random.standard_normal((self.lambda_, self.dim))
        arz = self.parent + self.sigma * numpy.dot(arz, self.A.T)
        return [ind_init(a) for a in arz]

    def update(self, population):
        """Update the current covariance matrix strategy from the
        *population*.

        :param population: A list of individuals from which to update the
                           parameters.
        """
        population.sort(key=lambda ind: ind.fitness, reverse=True)
        lambda_succ = sum(self.parent.fitness <= ind.fitness for ind in population)
        p_succ = float(lambda_succ) / self.lambda_
        self.psucc = (1 - self.cp) * self.psucc + self.cp * p_succ

        if self.parent.fitness <= population[0].fitness:
            x_step = (population[0] - numpy.array(self.parent)) / self.sigma
            self.parent = copy.deepcopy(population[0])
            if self.psucc < self.pthresh:
                self.pc = (1 - self.cc) * self.pc + sqrt(self.cc * (2 - self.cc)) * x_step
                self.C = (1 - self.ccov) * self.C + self.ccov * numpy.outer(self.pc, self.pc)
            else:
                self.pc = (1 - self.cc) * self.pc
                self.C = (1 - self.ccov) * self.C + self.ccov * (numpy.outer(self.pc, self.pc) + self.cc * (2 - self.cc) * self.C)

        self.sigma = self.sigma * exp(1.0 / self.d * (self.psucc - self.ptarg) / (1.0 - self.ptarg))

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
    """Multiobjective CMA-ES strategy based on the paper [Voss2010]_. It
    is used similarly as the standard CMA-ES strategy with a generate-update
    scheme.

    :param population: An initial population of individual.
    :param sigma: The initial step size of the complete system.
    :param mu: The number of parents to use in the evolution. When not
               provided it defaults to the length of *population*. (optional)
    :param lambda_: The number of offspring to produce at each generation.
                    (optional, defaults to 1)
    :param indicator: The indicator function to use. (optional, default to
                      :func:`~deap.tools.hypervolume`)

    Other parameters can be provided as described in the next table

    +----------------+---------------------------+----------------------------+
    | Parameter      | Default                   | Details                    |
    +================+===========================+============================+
    | ``d``          | ``1.0 + N / 2.0``         | Damping for step-size.     |
    +----------------+---------------------------+----------------------------+
    | ``ptarg``      | ``1.0 / (5 + 1.0 / 2.0)`` | Target success rate.       |
    +----------------+---------------------------+----------------------------+
    | ``cp``         | ``ptarg / (2.0 + ptarg)`` | Step size learning rate.   |
    +----------------+---------------------------+----------------------------+
    | ``cc``         | ``2.0 / (N + 2.0)``       | Cumulation time horizon.   |
    +----------------+---------------------------+----------------------------+
    | ``ccov``       | ``2.0 / (N**2 + 6.0)``    | Covariance matrix learning |
    |                |                           | rate.                      |
    +----------------+---------------------------+----------------------------+
    | ``pthresh``    | ``0.44``                  | Threshold success rate.    |
    +----------------+---------------------------+----------------------------+

    .. [Voss2010] Voss, Hansen, Igel, "Improved Step Size Adaptation
       for the MO-CMA-ES", 2010.

    """
    def __init__(self, population, sigma, **params):
        self.parents = population
        self.dim = len(self.parents[0])

        # Selection
        self.mu = params.get("mu", len(self.parents))
        self.lambda_ = params.get("lambda_", 1)

        # Step size control
        self.d = params.get("d", 1.0 + self.dim / 2.0)
        self.ptarg = params.get("ptarg", 1.0 / (5.0 + 0.5))
        self.cp = params.get("cp", self.ptarg / (2.0 + self.ptarg))

        # Covariance matrix adaptation
        self.cc = params.get("cc", 2.0 / (self.dim + 2.0))
        self.ccov = params.get("ccov", 2.0 / (self.dim ** 2 + 6.0))
        self.pthresh = params.get("pthresh", 0.44)

        # Internal parameters associated to the mu parent
        self.sigmas = [sigma] * len(population)
        # Lower Cholesky matrix (Sampling matrix)
        self.A = [numpy.identity(self.dim) for _ in range(len(population))]
        # Inverse Cholesky matrix (Used in the update of A)
        self.invCholesky = [numpy.identity(self.dim) for _ in range(len(population))]
        self.pc = [numpy.zeros(self.dim) for _ in range(len(population))]
        self.psucc = [self.ptarg] * len(population)

        self.indicator = params.get("indicator", tools.hypervolume)

    def generate(self, ind_init):
        r"""Generate a population of :math:`\lambda` individuals of type
        *ind_init* from the current strategy.

        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: A list of individuals with a private attribute :attr:`_ps`.
                  This last attribute is essential to the update function, it
                  indicates that the individual is an offspring and the index
                  of its parent.
        """
        arz = numpy.random.randn(self.lambda_, self.dim)
        individuals = list()

        # Make sure every parent has a parent tag and index
        for i, p in enumerate(self.parents):
            p._ps = "p", i

        # Each parent produce an offspring
        if self.lambda_ == self.mu:
            for i in range(self.lambda_):
                # print "Z", list(arz[i])
                individuals.append(ind_init(self.parents[i] + self.sigmas[i] * numpy.dot(self.A[i], arz[i])))
                individuals[-1]._ps = "o", i

        # Parents producing an offspring are chosen at random from the first front
        else:
            ndom = tools.sortLogNondominated(self.parents, len(self.parents), first_front_only=True)
            for i in range(self.lambda_):
                j = numpy.random.randint(0, len(ndom))
                _, p_idx = ndom[j]._ps
                individuals.append(ind_init(self.parents[p_idx] + self.sigmas[p_idx] * numpy.dot(self.A[p_idx], arz[i])))
                individuals[-1]._ps = "o", p_idx

        return individuals

    def _select(self, candidates):
        if len(candidates) <= self.mu:
            return candidates, []

        pareto_fronts = tools.sortLogNondominated(candidates, len(candidates))

        chosen = list()
        mid_front = None
        not_chosen = list()

        # Fill the next population (chosen) with the fronts until there is not enough space
        # When an entire front does not fit in the space left we rely on the hypervolume
        # for this front
        # The remaining fronts are explicitly not chosen
        full = False
        for front in pareto_fronts:
            if len(chosen) + len(front) <= self.mu and not full:
                chosen += front
            elif mid_front is None and len(chosen) < self.mu:
                mid_front = front
                # With this front, we selected enough individuals
                full = True
            else:
                not_chosen += front

        # Separate the mid front to accept only k individuals
        k = self.mu - len(chosen)
        if k > 0:
            # reference point is chosen in the complete population
            # as the worst in each dimension +1
            ref = numpy.array([ind.fitness.wvalues for ind in candidates]) * -1
            ref = numpy.max(ref, axis=0) + 1

            for _ in range(len(mid_front) - k):
                idx = self.indicator(mid_front, ref=ref)
                not_chosen.append(mid_front.pop(idx))

            chosen += mid_front

        return chosen, not_chosen

    def _rankOneUpdate(self, invCholesky, A, alpha, beta, v):
        w = numpy.dot(invCholesky, v)

        # Under this threshold, the update is mostly noise
        if w.max() > 1e-20:
            w_inv = numpy.dot(w, invCholesky)
            norm_w2 = numpy.sum(w ** 2)
            a = sqrt(alpha)
            root = numpy.sqrt(1 + beta / alpha * norm_w2)
            b = a / norm_w2 * (root - 1)

            A = a * A + b * numpy.outer(v, w)
            invCholesky = 1.0 / a * invCholesky - b / (a ** 2 + a * b * norm_w2) * numpy.outer(w, w_inv)

        return invCholesky, A

    def update(self, population):
        """Update the current covariance matrix strategies from the
        *population*.

        :param population: A list of individuals from which to update the
                           parameters.
        """
        chosen, not_chosen = self._select(population + self.parents)

        cp, cc, ccov = self.cp, self.cc, self.ccov
        d, ptarg, pthresh = self.d, self.ptarg, self.pthresh

        # Make copies for chosen offspring only
        last_steps = [self.sigmas[ind._ps[1]] if ind._ps[0] == "o" else None for ind in chosen]
        sigmas = [self.sigmas[ind._ps[1]] if ind._ps[0] == "o" else None for ind in chosen]
        invCholesky = [self.invCholesky[ind._ps[1]].copy() if ind._ps[0] == "o" else None for ind in chosen]
        A = [self.A[ind._ps[1]].copy() if ind._ps[0] == "o" else None for ind in chosen]
        pc = [self.pc[ind._ps[1]].copy() if ind._ps[0] == "o" else None for ind in chosen]
        psucc = [self.psucc[ind._ps[1]] if ind._ps[0] == "o" else None for ind in chosen]

        # Update the internal parameters for successful offspring
        for i, ind in enumerate(chosen):
            t, p_idx = ind._ps

            # Only the offspring update the parameter set
            if t == "o":
                # Update (Success = 1 since it is chosen)
                psucc[i] = (1.0 - cp) * psucc[i] + cp
                sigmas[i] = sigmas[i] * exp((psucc[i] - ptarg) / (d * (1.0 - ptarg)))

                if psucc[i] < pthresh:
                    xp = numpy.array(ind)
                    x = numpy.array(self.parents[p_idx])
                    pc[i] = (1.0 - cc) * pc[i] + sqrt(cc * (2.0 - cc)) * (xp - x) / last_steps[i]
                    invCholesky[i], A[i] = self._rankOneUpdate(invCholesky[i], A[i], 1 - ccov, ccov, pc[i])
                else:
                    pc[i] = (1.0 - cc) * pc[i]
                    pc_weight = cc * (2.0 - cc)
                    invCholesky[i], A[i] = self._rankOneUpdate(invCholesky[i], A[i], 1 - ccov + pc_weight, ccov, pc[i])

                self.psucc[p_idx] = (1.0 - cp) * self.psucc[p_idx] + cp
                self.sigmas[p_idx] = self.sigmas[p_idx] * exp((self.psucc[p_idx] - ptarg) / (d * (1.0 - ptarg)))

        # It is unnecessary to update the entire parameter set for not chosen individuals
        # Their parameters will not make it to the next generation
        for ind in not_chosen:
            t, p_idx = ind._ps

            # Only the offspring update the parameter set
            if t == "o":
                self.psucc[p_idx] = (1.0 - cp) * self.psucc[p_idx]
                self.sigmas[p_idx] = self.sigmas[p_idx] * exp((self.psucc[p_idx] - ptarg) / (d * (1.0 - ptarg)))

        # Make a copy of the internal parameters
        # The parameter is in the temporary variable for offspring and in the original one for parents
        self.parents = chosen
        self.sigmas = [sigmas[i] if ind._ps[0] == "o" else self.sigmas[ind._ps[1]] for i, ind in enumerate(chosen)]
        self.invCholesky = [invCholesky[i] if ind._ps[0] == "o" else self.invCholesky[ind._ps[1]] for i, ind in enumerate(chosen)]
        self.A = [A[i] if ind._ps[0] == "o" else self.A[ind._ps[1]] for i, ind in enumerate(chosen)]
        self.pc = [pc[i] if ind._ps[0] == "o" else self.pc[ind._ps[1]] for i, ind in enumerate(chosen)]
        self.psucc = [psucc[i] if ind._ps[0] == "o" else self.psucc[ind._ps[1]] for i, ind in enumerate(chosen)]


class StrategyActiveOnePlusLambda(object):
    r"""A CMA-ES strategy that combines the :math:`(1 + \lambda)` paradigm
    [Igel2007]_, the mixed integer modification [Hansen2011]_, active
    covariance update [Arnold2010]_ and constraint handling [Arnold2012]_.
    This version of CMA-ES requires the random vector and the mutation
    that created each individual. The vector and mutation are stored in each
    individual as :attr:`_z` and :attr:`_y` respectively. Updating with
    individuals not containing these attributes will result in an
    :class:`AttributeError`.
    Notes:
        When using this strategy (especially when using constraints) you should
        monitor the strategy :attr:`condition_number`. If it goes above a given
        threshold (say :math:`10^{12}`), you should think of restarting the
        optimization as the covariance matrix is going degenerate. See the
        constrained active CMA-ES example for a simple example of restart.
    :param parent: An iterable object that indicates where to start the
                   evolution. The parent requires a fitness attribute.
    :param sigma: The initial standard deviation of the distribution.
    :param step: The minimal step size for each dimension. Use 0 for
                 continuous dimensions.
    :param lambda_: Number of offspring to produce from the parent.
                    (optional, defaults to 1)
    :param **kwargs: One or more parameter to pass to the strategy as
                     described in the following table. (optional)
    +----------------+---------------------------+------------------------------+
    | Parameter      | Default                   | Details                      |
    +================+===========================+==============================+
    | ``d``          | ``1.0 + N / (2.0 *        | Damping for step-size.       |
    |                | lambda_)``                |                              |
    +----------------+---------------------------+------------------------------+
    | ``ptarg``      | ``1.0 / (5 + sqrt(lambda_)| Target success rate          |
    |                | / 2.0)``                  | (from 1 + lambda algorithm). |
    +----------------+---------------------------+------------------------------+
    | ``cp``         | ``ptarg * lambda_ / (2.0 +| Step size learning rate.     |
    |                | ptarg * lambda_)``        |                              |
    +----------------+---------------------------+------------------------------+
    | ``cc``         | ``2.0 / (N + 2.0)``       | Cumulation time horizon.     |
    +----------------+---------------------------+------------------------------+
    | ``ccov``       | ``2.0 / (N**2 + 6.0)``    | Covariance matrix learning   |
    |                |                           | rate.                        |
    +----------------+---------------------------+------------------------------+
    | ``ccovn``      | ``0.4 / (N**1.6 + 1.0)``  | Covariance matrix negative   |
    |                |                           | learning rate.               |
    +----------------+---------------------------+------------------------------+
    | ``cconst``     | ``1.0 / (N + 2.0)``       | Constraint vectors learning  |
    |                |                           | rate.                        |
    +----------------+---------------------------+------------------------------+
    | ``beta``       | ``0.1 / (lambda_ * (N +   | Covariance matrix learning   |
    |                |   2.0))``                 | rate for constraints.        |
    |                |                           |                              |
    +----------------+---------------------------+------------------------------+
    | ``pthresh``    | ``0.44``                  | Threshold success rate.      |
    +----------------+---------------------------+------------------------------+
    .. [Igel2007] Igel, Hansen and Roth. Covariance matrix adaptation for
       multi-objective optimization. 2007
    .. [Arnold2010] Arnold and Hansen. Active covariance matrix adaptation for
       the (1+1)-CMA-ES. 2010.
    .. [Hansen2011] Hansen. A CMA-ES for Mixed-Integer Nonlinear Optimization.
       Research Report] RR-7751, INRIA. 2011
    .. [Arnold2012] Arnold and Hansen. A (1+1)-CMA-ES for Constrained Optimisation.
       2012
    """
    def __init__(self, parent, sigma, steps, **kargs):
        self.parent = parent
        self.sigma = sigma
        self.dim = len(self.parent)

        self.A = numpy.identity(self.dim)
        self.invA = numpy.identity(self.dim)
        self.condition_number = numpy.linalg.cond(self.A)

        self.pc = numpy.zeros(self.dim)

        # Save parameters
        self.params = kargs.copy()

        # Covariance matrix adaptation
        self.cc = self.params.get("cc", 2.0 / (self.dim + 2.0))
        self.ccovp = self.params.get("ccovp", 2.0 / (self.dim ** 2 + 6.0))
        self.ccovn = self.params.get("ccovn", 0.4 / (self.dim ** 1.6 + 1.0))
        self.cconst = self.params.get("cconst", 1.0 / (self.dim + 2.0))
        self.pthresh = self.params.get("pthresh", 0.44)

        self.lambda_ = self.params.get("lambda_", 1)

        self.psucc = self.ptarg
        self.S_int = numpy.array(steps)
        self.i_I_R = numpy.flatnonzero(2 * self.sigma * numpy.diag(self.A)**0.5
                                       < self.S_int)

        self.constraint_vecs = None
        self.ancestors_fitness = list()

    @property
    def lambda_(self):
        return self._lambda

    @lambda_.setter
    def lambda_(self, value):
        self._lambda = value
        self._compute_lambda_parameters()

    def _compute_lambda_parameters(self):
        r"""Computes the parameters depending on :math:`\lambda`. It needs to
        be called again if :math:`\lambda` changes during evolution.
        """
        # Step size control :
        self.d = self.params.get("d", 1.0 + self.dim / (2.0 * self.lambda_))
        self.ptarg = self.params.get("ptarg", 1.0 / (5 + numpy.sqrt(self.lambda_)
                                                     / 2.0))
        self.cp = self.params.get("cp", (self.ptarg * self.lambda_
                                         / (2 + self.ptarg * self.lambda_)))

        self.beta = self.params.get("beta", 0.1 / (self.lambda_ * (self.dim + 2.0)))

    def generate(self, ind_init):
        r"""Generate a population of :math:`\lambda` individuals of type
        *ind_init* from the current strategy.
        :param ind_init: A function object that is able to initialize an
                         individual from a list.
        :returns: A list of individuals.
        """
        # Generate individuals
        z = numpy.random.standard_normal((self.lambda_, self.dim))
        y = numpy.dot(self.A, z.T).T
        x = self.parent + self.sigma * y + self.S_int * self._integer_mutation()

        if any(self.S_int > 0):
            # Bring values to the integer steps
            round_values = numpy.tile(self.S_int > 0, (self.lambda_, 1))
            steps = numpy.tile(self.S_int, (self.lambda_, 1))
            x[round_values] = steps[round_values] * numpy.around(x[round_values]
                                                                 / steps[round_values])

        # The update method requires to remember the y of each individual
        population = list(map(ind_init, x))
        for ind, yi, zi in zip(population, y, z):
            ind._y = yi
            ind._z = zi

        return population

    def _integer_mutation(self):
        n_I_R = self.i_I_R.shape[0]

        # Mixed integer CMA-ES is developed for (mu/mu , lambda)
        # We have a (1 + lambda) setting, thus we make the integer mutation
        # probabilistic. The integer mutation is lambda / 2 if all dimensions
        # are integers or min(lambda / 2 - 1, lambda / 10 + n_I_R + 1). The minus
        # 1 accounts for the last new candidate getting its integer mutation from
        # the last best solution. We skip this last best solution part.
        if n_I_R == 0:
            return numpy.zeros((self.lambda_, self.dim))
        elif n_I_R == self.dim:
            p = self.lambda_ / 2.0 / self.lambda_
            # lambda_int = int(numpy.floor(self.lambda_ / 2))
        else:
            p = (min(self.lambda_ / 2.0, self.lambda_ / 10.0 + n_I_R / self.dim)
                 / self.lambda_)
            # lambda_int = int(min(numpy.floor(self.lambda_ / 10) + n_I_R + 1,
            #                      numpy.floor(self.lambda_ / 2) - 1))

        Rp = numpy.zeros((self.lambda_, self.dim))
        Rpp = numpy.zeros((self.lambda_, self.dim))

        # Ri' has exactly one of its components set to one.
        # The Ri' are dependent in that the number of mutations for each coordinate
        # differs at most by one
        for i, j in zip(range(self.lambda_), cycle(self.i_I_R)):
            # Probabilistically choose lambda_int individuals
            if numpy.random.rand() < p:
                Rp[i, j] = 1
                Rpp[i, j] = numpy.random.geometric(p=0.7**(1.0 / n_I_R)) - 1

        I_pm1 = (-1)**numpy.random.randint(0, 2, (self.lambda_, self.dim))
        R_int = I_pm1 * (Rp + Rpp)

        # Usually in mu/mu, lambda the last individual is set to the step taken.
        # We don't use this scheme in the 1 + lambda scheme
        # if self.update_count > 0:
        #     R_int[-1, :] = (numpy.floor(-self.S_int - self.last_best)
        #                     - numpy.floor(-self.S_int - self.centroid))

        return R_int

    def _rank1update(self, individual, p_succ):
        update_cov = False
        self.psucc = (1 - self.cp) * self.psucc + self.cp * p_succ

        if not hasattr(self.parent, "fitness") \
                or self.parent.fitness <= individual.fitness:
            self.parent = copy.deepcopy(individual)
            self.ancestors_fitness.append(copy.deepcopy(individual.fitness))
            if len(self.ancestors_fitness) > 5:
                self.ancestors_fitness.pop()

            # Must guard if pc is all 0 to prevent w_norm_sqrd to be 0
            if self.psucc < self.pthresh or numpy.allclose(self.pc, 0):
                self.pc = (1 - self.cc) * self.pc + (numpy.sqrt(self.cc * (2 - self.cc))
                                                     * individual._y)

                a = numpy.sqrt(1 - self.ccovp)
                w = numpy.dot(self.invA, self.pc)
                w_norm_sqrd = numpy.linalg.norm(w) ** 2
                b = numpy.sqrt(1 - self.ccovp) / w_norm_sqrd \
                    * (numpy.sqrt(1 + self.ccovp / (1 - self.ccovp) * w_norm_sqrd)
                       - 1)

            else:
                self.pc = (1 - self.cc) * self.pc

                d = self.ccovp * (1 + self.cc * (2 - self.cc))
                a = numpy.sqrt(1 - d)
                w = numpy.dot(self.invA, self.pc)
                w_norm_sqrd = numpy.linalg.norm(w) ** 2
                b = numpy.sqrt(1 - d) \
                    * (numpy.sqrt(1 + self.ccovp * w_norm_sqrd / (1 - d)) - 1) \
                    / w_norm_sqrd

            update_cov = True

        elif len(self.ancestors_fitness) >= 5 \
                and individual.fitness < self.ancestors_fitness[0] \
                and self.psucc < self.pthresh:
            # Active covariance update requires w = z and not w = inv(A)s
            w = individual._z
            w_norm_sqrd = numpy.linalg.norm(w) ** 2
            if 1 < self.ccovn * (2 * w_norm_sqrd - 1):
                ccovn = 1 / (2 * w_norm_sqrd - 1)
            else:
                ccovn = self.ccovn

            a = numpy.sqrt(1 + ccovn)
            b = numpy.sqrt(1 + ccovn) / w_norm_sqrd \
                * (numpy.sqrt(1 - ccovn / (1 + ccovn) * w_norm_sqrd) - 1)
            update_cov = True

        if update_cov:
            self.A = self.A * a + b * numpy.outer(numpy.dot(self.A, w), w)
            self.invA = (1 / a * self.invA
                         - b / (a ** 2 + a * b * w_norm_sqrd)
                         * numpy.dot(self.invA, numpy.outer(w, w)))

        # TODO: Add integer mutation i_I_R component
        self.sigma = self.sigma * numpy.exp(1.0 / self.d
                                            * ((self.psucc - self.ptarg)
                                               / (1.0 - self.ptarg)))

    def _infeasible_update(self, individual):
        if not hasattr(individual.fitness, "constraint_violation"):
            return

        if self.constraint_vecs is None:
            shape = len(individual.fitness.constraint_violation), self.dim
            self.constraint_vecs = numpy.zeros(shape)

        for i in range(self.constraint_vecs.shape[0]):
            if individual.fitness.constraint_violation[i]:
                self.constraint_vecs[i] = (1 - self.cconst) * self.constraint_vecs[i] \
                    + self.cconst * individual._y

        W = numpy.dot(self.invA, self.constraint_vecs.T).T  # M x N
        constraint_violation = numpy.sum(individual.fitness.constraint_violation)

        A_prime = (
            self.A - self.beta / constraint_violation
            * numpy.sum(
                list(
                    numpy.outer(self.constraint_vecs[i], W[i])
                    / numpy.dot(W[i], W[i])
                    for i in range(self.constraint_vecs.shape[0])
                    if individual.fitness.constraint_violation[i]
                ),
                axis=0
            )
        )

        try:
            self.invA = numpy.linalg.inv(A_prime)
        except numpy.linalg.LinAlgError:
            warnings.warn("Singular matrix inversion, "
                          "invalid update in CMA-ES ignored", RuntimeWarning)
        else:
            self.A = A_prime

    def update(self, population):
        """Update the current covariance matrix strategy from the *population*.
        :param population: A list of individuals from which to update the
                           parameters.
        """
        valid_population = [ind for ind in population if ind.fitness.valid]
        invalid_population = [ind for ind in population if not ind.fitness.valid]

        if len(valid_population) > 0:
            # Rank 1 update
            valid_population.sort(key=lambda ind: ind.fitness, reverse=True)
            if not hasattr(self.parent, "fitness"):
                lambda_succ = len(valid_population)
            else:
                lambda_succ = sum(self.parent.fitness <= ind.fitness
                                  for ind in valid_population)
            # Use len(valid) to not account for individuals violating constraints
            self._rank1update(valid_population[0],
                              float(lambda_succ) / len(valid_population))

        if len(invalid_population) > 0:
            # Learn constraint from all invalid individuals
            for ind in invalid_population:
                self._infeasible_update(ind)

        # Used to monitor the convariance matrix conditioning
        self.condition_number = numpy.linalg.cond(self.A)

        C = numpy.dot(self.A, self.A.T)
        self.i_I_R = numpy.flatnonzero(2 * self.sigma * numpy.diag(C)**0.5
                                       < self.S_int)
