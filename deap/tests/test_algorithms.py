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
import unittest

from deap import algorithms
from deap import base
from deap import benchmarks
from deap import cma
from deap import creator
from deap import tools

FITCLSNAME = "FIT_TYPE"
INDCLSNAME = "IND_TYPE"

    
def setup_func():
    creator.create(FITCLSNAME, base.Fitness, weights=(-1.0,))
    creator.create(INDCLSNAME, list, fitness=creator.__dict__[FITCLSNAME])

def teardown_func():
    del creator.__dict__[FITCLSNAME]
    del creator.__dict__[INDCLSNAME]

@with_setup(setup_func, teardown_func)
def test_cma():
    N = 5

    strategy = cma.Strategy(centroid=[0.0]*N, sigma=1.0)
    
    toolbox = base.Toolbox()
    toolbox.register("evaluate", benchmarks.sphere)
    toolbox.register("generate", strategy.generate, creator.__dict__[INDCLSNAME])
    toolbox.register("update", strategy.update)

    pop, _ = algorithms.eaGenerateUpdate(toolbox, ngen=100)
    best, = tools.selBest(pop, k=1)

    assert best.fitness.values < (1e-8,), "CMA algorithm did not converged properly."
