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
"""
The :mod:`wfg` module provides an implementation of the Walking Fish Group
multi-objective optimization problem toolkit.

Checkout https://github.com/lmarti/wfg-deap for examples.
"""

from functools import reduce
from math import fabs, ceil, floor, sin, cos, pi
from operator import mul
from copy import deepcopy

import numpy as np


def create_instance_wfg1(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG1 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417
    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG1 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError - if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG1 with 6 distance parameters, 9 position
        parameters and 3 objectives:
        >>> wfg1_func, (bounds_low, bounds_high) = create_instance_wfg1(6, 9, 3)
        >>> toolbox.register('evaluate', wfg1_func)
    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.
        The following restrictions on the parameters should be:
        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg1', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg2(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG2 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417
    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG2 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError - if an incorrect parameter is detected.
    
    Example:
        Creating an instance of WFG2 with 6 distance parameters, 9 position
        parameters and 3 objectives:
        >>> wfg2_func, (bounds_low, bounds_high) = create_instance_wfg2(6, 9, 3)
        >>> toolbox.register('evaluate', wfg2_func)
    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.
        The following restrictions on the parameters should be:
        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg2', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg3(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG3 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417
    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.
    
    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG3 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError - if an incorrect parameter is detected.
    Example:
        Creating an instance of WFG3 with 6 distance parameters, 9 position
        parameters and 3 objectives:
        >>> wfg3_func, (bounds_low, bounds_high) = create_instance_wfg3(6, 9, 3)
        >>> toolbox.register('evaluate', wfg3_func)
    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.
        The following restrictions on the parameters should be:
        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg3', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg4(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG4 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417

    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG4 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError - if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG4 with 6 distance parameters, 9 position parameters and 3 objectives:
        >>> wfg4_func, (bounds_low, bounds_high) = create_instance_wfg4(6, 9, 3)
        >>> toolbox.register('evaluate', wfg4_func)

    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.

        The following restrictions on the parameters should be :

        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg4', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg5(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG5 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417

    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG5 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError - if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG5 with 6 distance parameters, 9 position parameters and 3 objectives:
        >>> wfg5_func, (bounds_low, bounds_high) = create_instance_wfg5(6, 9, 3)
        >>> toolbox.register('evaluate', wfg5_func)

    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.

        The following restrictions on the parameters should be :

        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg5', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg6(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG6 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417

    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG6 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError -if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG6 with 6 distance parameters, 9 position parameters and 3 objectives:
        >>> wfg6_func, (bounds_low, bounds_high) = create_instance_wfg6(6, 9, 3)
        >>> toolbox.register('evaluate', wfg6_func)

    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.

        The following restrictions on the parameters should be :

        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg6', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg7(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG7 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417

    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG7 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError - if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG7 with 6 distance parameters, 9 position parameters and 3 objectives:
        >>> wfg7_func, (bounds_low, bounds_high) = create_instance_wfg7(6, 9, 3)
        >>> toolbox.register('evaluate', wfg7_func)

    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.

        The following restrictions on the parameters should be :

        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg7', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg8(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG8 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417

    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds)` where:
    * func: the function that evaluates an individual using the WFG8 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError - if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG8 with 6 distance parameters, 9 position parameters and 3 objectives:
        >>> wfg8_func, (bounds_low, bounds_high) = create_instance_wfg8(6, 9, 3)
        >>> toolbox.register('evaluate', wfg8_func)

    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.

        The following restrictions on the parameters should be :

        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg8', num_distance_params, num_position_params, num_objectives)

def create_instance_wfg9(num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG9 problem.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417

    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds, sol_gen_func)` where:
    * func: the function that evaluates an individual using the WFG9 problem function.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.

    :raises: ValueError if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG9 with 6 distance parameters, 9 position parameters and 3 objectives:
        >>> wfg9_func, (bounds_low, bounds_high) = create_instance_wfg9(6, 9, 3)
        >>> toolbox.register('evaluate', wfg9_func)

    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.

        The following restrictions on the parameters should be :

        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    return _wfg_problem_instance('wfg9', num_distance_params, num_position_params, num_objectives)

def _wfg_problem_instance(problem_name, num_distance_params, num_position_params, num_objectives):
    """Creates an instance of one of the WFG problems.
    From: Huband, S., Hingston, P., Barone, L., & While, L. (2006).
    A review of multiobjective test problems and a scalable test problem toolkit.
    IEEE Transactions on Evolutionary Computation, 10(5), 477-506. doi:10.1109/TEVC.2005.861417

    :param problem_name: name of the instance to create ('wfg1',...,'wfg9').
    :param num_distance_params: number of distance parameters.
    :param num_position_params: number of position parameters.
    :param num_objectives: number of objectives.

    :returns: A tuple of the form `(func, bounds, sol_gen_func)` where:
    * func: the function that evaluates an individual using the correspoding problem instance.
    * bounds: a tuple containing the lower and higher bounds of the problem feasible space.
    * sol_gen_func: a function that generates an optimal solution of the problem at a random
    * location of the Pareto optimal front.

    :raises: ValueError - if an incorrect parameter is detected.

    Example:
        Creating an instance of WFG4 with 6 distance parameters, 9 position parameters and 3 objectives:
        >>> wfg4_func, (bounds_low, bounds_high, wfg4_sol = wfg_problem_instance('wfg4', 6, 9, 3)

    .. note::
        The number of variables of the problem is ``num_distance_params`` + ``num_position_params``.

        The following restrictions on the parameters should be :

        * WFG problems must have two or more objectives.
        * ``num_position_params`` % (``num_objectives``-1) = 0.
        * ``num_position_params`` >=4.
        * ``num_distance_params`` + ``num_position_params`` >= ``num_objectives``.
        * In WFG2 and WFG3 ``num_distance_params`` must be divisible by 2.
        * Checkout https://github.com/lmarti/wfg-deap for usage examples.
    """
    problem = _WFG_Problem_Factory(problem_name, num_distance_params, num_position_params, num_objectives)
    return problem.instance()

class _WFG_Problem_Factory():
    'A class that encapsulates the WFG-related functionallity.'

    def __init__(self, problem_name, num_distance, num_position, num_objectives):
        self.problems = {'wfg1': self.evaluate_wfg1,
                         'wfg2': self.evaluate_wfg2,
                         'wfg3': self.evaluate_wfg3,
                         'wfg4': self.evaluate_wfg4,
                         'wfg5': self.evaluate_wfg5,
                         'wfg6': self.evaluate_wfg6,
                         'wfg7': self.evaluate_wfg7,
                         'wfg8': self.evaluate_wfg8,
                         'wfg9': self.evaluate_wfg9}

        self.validate_wfg_parameters(problem_name, num_distance, num_position, num_objectives)
        self.problem_name = problem_name
        self.l = num_distance                        # number of distance-related parameters
        self.k = num_position                        # number of position-related parameters
        self.num_vars = num_position + num_distance  # number of problem variables
        self.num_objs = num_objectives               # number of objectives

        self.S = range(2, 2 * num_objectives + 1, 2) # scaling constants vector
        self.A = [1.0] * (num_objectives - 1)        # degeneracy constants vector
        # self.vec_aux = [1.0] * self.num_vars

    def validate_wfg_parameters(self, problem_name, l, k, m):
        if not problem_name in self.problems:
            raise KeyError('Problem name `' + problem_name + "' is not part of the WFG toolkit.")
        if m < 2:
            raise ValueError('WFG problems must have two or more objectives.')
        if not k % (m - 1) == 0:
            raise ValueError('Position parameter (k) must be divisible by number of objectives minus one.')
        if k < 4:
            raise ValueError('Position parameter (k) must be greater or equal than 4.')
        if (k + l) < m:
            raise ValueError('Sum of distance and position parameters must be greater than num. of objs. (k + l >= M).')
        if problem_name in ('wfg2', 'wfg3') and not l % 2 == 0:
            raise ValueError('In WFG2/WFG3 the distance-related parameter (l) must be divisible by 2.')
        return True

    def destep(self, vec):
        'Removes the [2, 4, 6,...] steps.'
        return np.divide(vec, [2.0 * (i + 1) for i in range(len(vec))])

    def step_up(self, vec):
        'Introduces the [2, 4, 6,...] steps.'
        return np.multiply(vec, list([2 * (i + 1) for i in range(len(vec))]))

    def get_bounds(self):
        return [0.0] * self.num_vars, [2.0 * (i + 1) for i in range(self.num_vars)]

    def instance(self):
        return self.problems[self.problem_name], self.get_bounds()

    def estimate_vec_x(self, t, a):
        x = [max(t[-1], a[i]) * (t[i] - 0.5) + 0.5 for i in range(len(t) - 1)]
        x.append(t[-1])
        return x

    def calculate_objectives(self, x, s, h):
        return [x[-1] + s[i] * h[i] for i in range(len(s))]

    def evaluate_wfg1(self, individual):
        ind = self.destep(individual)

        for i in range(self.k, self.num_vars):
            ind[i] = _transformation_shift_linear(ind[i], 0.35)

        for i in range(self.k, self.num_vars):
            ind[i] = _transformation_bias_flat(ind[i], 0.8, 0.75, 0.85)

        for i in range(self.num_vars):
            ind[i] = np.nan_to_num(_transformation_bias_poly(ind[i], 0.02))

        # set of last transition values
        w = range(2, 2 * self.num_vars + 1, 2)
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_weighted_sum(ind[(m - 1) * gap : (m * gap)], w[(m - 1) * gap : (m * gap)]) for m in range(1, self.num_objs)]
        t.append(_reduction_weighted_sum(ind[self.k:self.num_vars], w[self.k:self.num_vars]))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_convex(x[:-1], m + 1) for m in range(self.num_objs - 1)]
        h.append(_shape_mixed(x[0]))

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg2(self, individual):
        ind = self.destep(individual)

        ind_non_sep = self.k + self.l // 2
        ind_r_sum = ind_non_sep

        for i in range(self.k, self.num_vars):
            ind[i] = _transformation_shift_linear(ind[i], 0.35)

        for i in range(self.k, ind_non_sep - 1):
            head = (2 * i) - self.k
            tail = head + 1
            ind[i] = _reduction_non_sep((ind[head], ind[tail]), 2)

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_weighted_sum(ind[(m - 1) * gap : (m * gap)], [1.0] * gap) for m in range(1, self.num_objs)]
        t.append(_reduction_weighted_sum(ind[self.k:ind_r_sum], [1.0] * (ind_r_sum - self.k)))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_convex(x[:-1], m + 1) for m in range(self.num_objs - 1)]
        h.append(_shape_disconnected(x[0]))

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg3(self, individual):
        ind = self.destep(individual)

        wfg3_a = [1.0] * (self.num_objs - 1)

        if self.num_objs > 2:
            wfg3_a[1:] = [0.0] * (self.num_objs - 2)

        ind_non_sep = self.k + self.l // 2
        ind_r_sum = ind_non_sep

        for i in range(self.k, self.num_vars):
            ind[i] = _transformation_shift_linear(ind[i], 0.35)

        for i in range(self.k, ind_non_sep - 1):
            head = (2 * i) - self.k
            tail = head + 1
            ind[i] = _reduction_non_sep((ind[head], ind[tail]), 2)

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_weighted_sum(ind[(m - 1) * gap : (m * gap)], [1.0] * gap) for m in range(1, self.num_objs)]
        t.append(_reduction_weighted_sum(ind[self.k:ind_r_sum], [1.0] * (ind_r_sum - self.k)))

        x = self.estimate_vec_x(t, wfg3_a)

        # computation of shape vector
        h = [_shape_linear(x[:-1], m + 1) for m in range(self.num_objs)] 

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg4(self, individual):
        ind = self.destep(individual)
        ind = [_transformation_shift_multi_modal(item, 30.0, 10.0, 0.35) for item in ind]#5.0, 10.0, 0.35

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_weighted_sum(ind[(m - 1) * gap : (m * gap)], [1.0] * gap) for m in range(1, self.num_objs)]
        t.append(_reduction_weighted_sum(ind[self.k:], [1.0] * (self.num_vars - self.k)))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_concave(x[:-1], m + 1) for m in range(self.num_objs)]

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg5(self, individual):
        ind = self.destep(individual)
        ind = [_transformation_param_deceptive(item) for item in ind]

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_weighted_sum(ind[(m - 1) * gap : (m * gap)], [1.0] * gap) for m in range(1, self.num_objs)]
        t.append(_reduction_weighted_sum(ind[self.k:], [1.0] * (self.num_vars - self.k)))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_concave(x[:-1], m + 1) for m in range(self.num_objs)]

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg6(self, individual):
        ind = self.destep(individual)

        for i in range(self.k, self.num_vars):
            ind[i] = _transformation_shift_linear(ind[i], 0.35)

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_non_sep(ind[(m - 1) * gap : (m * gap)], gap) for m in range(1, self.num_objs)]
        t.append(_reduction_non_sep(ind[self.k:], self.l))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_concave(x[:-1], m + 1) for m in range(self.num_objs)]

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg7(self, individual):
        ind = self.destep(individual)
        copy_ind = deepcopy(ind)
        ones = [1.0] * self.num_vars

        for i in range(self.k):
            aux = _reduction_weighted_sum(copy_ind[i + 1:], ones[i + 1:])
            ind[i] = _transformation_param_dependent(ind[i], aux)

        for i in range(self.k, self.num_vars):
            ind[i] = _transformation_shift_linear(ind[i], 0.35)

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_weighted_sum(ind[(m - 1) * gap : (m * gap)], [1.0] * gap) for m in range(1, self.num_objs)]
        t.append(_reduction_weighted_sum(ind[self.k:], [1.0] * (self.num_vars - self.k)))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_concave(x[:-1], m + 1) for m in range(self.num_objs)]  # Shape vector computation

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg8(self, individual):
        ind = self.destep(individual)
        copy_ind = deepcopy(ind)
        ones = [1.0] * self.num_vars

        for i in range(self.k, self.num_vars):
            aux = _reduction_weighted_sum(copy_ind[:i], ones[:i])
            ind[i] = _transformation_param_dependent(ind[i], aux)

        for i in range(self.k, self.num_vars):
            ind[i] = _transformation_shift_linear(ind[i], 0.35)

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_weighted_sum(ind[(m - 1) * gap : (m * gap)], [1.0] * gap) for m in range(1, self.num_objs)]
        t.append(_reduction_weighted_sum(ind[self.k:], [1.0] * (self.num_vars - self.k)))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_concave(x[:-1], m + 1) for m in range(self.num_objs)]  # Shape vector computation

        return self.calculate_objectives(x, self.S, h)

    def evaluate_wfg9(self, individual):
        ind = self.destep(individual)
        copy_ind = deepcopy(ind)

        # vec_aux = [1.0]*self._length
        for i in range(0, self.num_vars - 1):
            aux = _reduction_weighted_sum(copy_ind[i + 1:], [1.0] * (self.num_vars - i - 1))
            ind[i] = _transformation_param_dependent(ind[i], aux)

        a = [_transformation_shift_deceptive(ind[i]) for i in range(self.k)]
        b = [_transformation_shift_multi_modal(ind[i], 5.0, 10.0, 0.35) for i in range(self.k, self.num_vars)]#30.0, 95.0, 0.35
        ind = a + b

        # set of last transition values
        gap = self.k // (self.num_objs - 1)
        t = [_reduction_non_sep(ind[(m - 1) * gap : (m * gap)], gap) for m in range(1, self.num_objs)]
        t.append(_reduction_non_sep(ind[self.k:], self.l))

        x = self.estimate_vec_x(t, self.A)

        # computation of shape vector
        h = [_shape_concave(x[:-1], m + 1) for m in range(self.num_objs)]  # Shape vector computation

        return self.calculate_objectives(x, self.S, h)

def _transformation_shift_linear(value, shift=0.35):
    'Linear shift transformation.'
    return fabs(value - shift) / fabs(floor(shift - value) + shift)

def _transformation_shift_deceptive(y, A=0.35, B=0.005, C=0.05):
    'Shift: Parameter Deceptive Transformation.'
    tmp1 = floor(y - A + B) * (1.0 - C + (A - B) / B) / (A - B)
    tmp2 = floor(A + B - y) * (1.0 - C + (1.0 - A - B) / B) / (1.0 - A - B)
    return 1.0 + (fabs(y - A) - B) * (tmp1 + tmp2 + 1.0 / B)

def _transformation_shift_multi_modal(y, A, B, C):
    'Shift: Parameter Multi-Modal Transformation.'
    tmp1 = fabs(y - C) / (2.0 * (floor(C - y) + C))
    tmp2 = (4.0 * A + 2.0) * pi * (0.5 - tmp1)
    return (1.0 + cos(tmp2) + 4.0 * B * pow(tmp1, 2.0)) / (B + 2.0)

def _transformation_bias_flat(value, a, b, c):
    'Flat bias region transformation.'
    tmp1 = min(0.0, floor(value - b))* (a * (b - value) / b)
    tmp2 = min(0.0, floor(c - value))* ((1.0 - a) * (value - c) / (1.0 - c))
    return a + tmp1 - tmp2

def _transformation_bias_poly(y, alpha):
    'Polynomial bias transformation.'
    aux = y ** alpha
    return aux

def _transformation_param_dependent(y, y_deg, A=0.98/49.98, B=0.02, C=50.0):
    'Parameter dependent bias transformation.'
    aux = A - (1.0 - 2.0 * y_deg) * fabs(floor(0.5 - y_deg) + A)
    return pow(y, B + (C - B) * aux)

def _transformation_param_deceptive(y, A=0.35, B=0.001, C=0.05):
    'Shift: Parameter Deceptive Transformation.'
    tmp1 = floor(y - A + B) * (1.0 - C + (A - B) / B) / (A - B)
    tmp2 = floor(A + B - y) * (1.0 - C + (1.0 - A - B) / B) / (1.0 - A - B)
    return 1.0 + (fabs(y - A) - B) * (tmp1 + tmp2 + 1.0 / B)

def _reduction_weighted_sum(y, w):
    'Weighted sum reduction transformation.'
    return np.dot(y, w) / sum(w)

def _reduction_non_sep(y, A):
    'Non-Separable reduction transformation.'
    numerator = 0.0
    for j in range(len(y)):
        numerator += y[j]
        for k in range(A - 1):  # To verify the constant (1 or 2)
            numerator += fabs(y[j] - y[(1 + j + k) % len(y)])
    tmp = ceil(A / 2.0)
    denominator = len(y) * tmp * (1.0 + 2.0 * A - 2 * tmp) / A
    return numerator / denominator

def _shape_convex(x, m):
    'Convex Pareto front shape function.'
    if m == 1:
        result = reduce(mul, (1.0 - cos(0.5 * xi * pi) for xi in x[:len(x)]), 1.0)
    elif 1 < m <= len(x):
        result = reduce(mul, (1.0 - cos(0.5 * xi * pi) for xi in x[:len(x) - m + 1]), 1.0)
        result *= 1.0 - sin(0.5 * x[len(x) - m + 1] * pi)
    else:
        result = 1.0 - sin(0.5 * x[0] * pi)
    return result

def _shape_mixed(x, A=5.0, alpha=1.0):
    'Convex/concave mixed Pareto front shape function.'
    aux = 2.0 * A * pi
    return pow(1.0 - x - (cos(aux * x + 0.5 * pi) / aux), alpha)

def _shape_disconnected(x, alpha=1.0, beta=1.0, A=5.0):
    'Disconnected Pareto front shape function.'
    aux = cos(A * pi * pow(x, beta))
    return 1.0 - pow(x, alpha) * pow(aux, 2)

def _shape_linear(x, m):
    'Linear Pareto optimal front shape function.'
    if m == 1:
        result = reduce(mul, (xi for xi in x[:len(x)]), 1.0)
    elif 1 < m <= len(x):
        result = reduce(mul, (xi for xi in x[:len(x) - m + 1]), 1.0)
        result *= (1.0 - x[len(x) - m + 1])
    else:
        result = 1.0 - x[0]
    return result

def _shape_concave(x, m):
    'Concave Pareto optimal shape function.'
    if m == 1:
        result = reduce(mul, (sin(0.5 * xi * pi) for xi in x[:len(x)]), 1.0)
    elif 1 < m <= len(x):
        result = reduce(mul, (sin(0.5 * xi * pi) for xi in x[:len(x) - m + 1]), 1.0)
        result *= cos(0.5 * x[len(x) - m + 1] * pi)
    else:
        result = cos(0.5 * x[0] * pi)
    return result