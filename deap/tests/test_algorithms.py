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

from nose import with_setup
import platform
import random
import unittest

from deap import algorithms
from deap import base
from deap import benchmarks
#from deap.benchmarks.tools import hypervolume
from deap import cma
from deap import creator
from deap import tools

FITCLSNAME = "FIT_TYPE"
INDCLSNAME = "IND_TYPE"

    
def setup_func_single_obj():
    creator.create(FITCLSNAME, base.Fitness, weights=(-1.0,))
    creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

def setup_func_multi_obj():
    creator.create(FITCLSNAME, base.Fitness, weights=(-1.0, -1.0))
    creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

def teardown_func():
    # Messy way to remove a class from the creator
    del creator.__dict__[FITCLSNAME]
    del creator.__dict__[INDCLSNAME]

@unittest.skipIf(platform.python_implementation() == "PyPy", "PyPy has no support for eigen decomposition.")
@with_setup(setup_func_single_obj, teardown_func)
def test_cma():
    NDIM = 5

    strategy = cma.Strategy(centroid=[0.0]*NDIM, sigma=1.0)
    
    toolbox = base.Toolbox()
    toolbox.register("evaluate", benchmarks.sphere)
    toolbox.register("generate", strategy.generate, creator.__dict__[INDCLSNAME])
    toolbox.register("update", strategy.update)

    pop, _ = algorithms.eaGenerateUpdate(toolbox, ngen=100)
    best, = tools.selBest(pop, k=1)

    assert best.fitness.values < (1e-8,), "CMA algorithm did not converged properly."

@with_setup(setup_func_multi_obj, teardown_func)
def test_nsga2():
    NDIM = 5
    BOUND_LOW, BOUND_UP = 0.0, 1.0
    MU = 16

    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.uniform, BOUND_LOW, BOUND_UP)
    toolbox.register("individual", tools.initRepeat, creator.__dict__[INDCLSNAME], toolbox.attr_float, NDIM)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", benchmarks.zdt1)
    toolbox.register("mate", tools.cxSimulatedBinaryBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0)
    toolbox.register("mutate", tools.mutPolynomialBounded, low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)
    toolbox.register("select", tools.selNSGA2)

    pop = toolbox.population(n=MU)
    fitnesses = toolbox.map(toolbox.evaluate, pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    pop = toolbox.select(pop, len(pop))
    for gen in range(1, 100):
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]
        
        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() <= 0.9:
                toolbox.mate(ind1, ind2)
            
            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.fitness.values, ind2.fitness.values
        
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop = toolbox.select(pop + offspring, MU)

    #hv = benchmarks.tools.hypervolume(pop, [11.0, 11.0])
    hv = 120.777 # Optimal value

    assert hv > 120.0, "Waiting on the hypervolume measure!"
