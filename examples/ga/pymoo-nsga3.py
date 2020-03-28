from math import factorial

from pymoo.indicators.igd import IGD
from pymoo.optimize import minimize
from pymoo.util import plotting
from pymoo.util.reference_direction import UniformReferenceDirectionFactory
from pymop.factory import get_problem
from pymoo.algorithms.nsga3 import nsga3
import matplotlib.pyplot as plt
import numpy

from deap.benchmarks.tools import igd


PROBLEM = "dtlz1"
NOBJ = 3
K = 5
NDIM = NOBJ + K - 1
P = 12
H = factorial(NOBJ + P - 1) / (factorial(P) * factorial(NOBJ - 1))
MU = int(H + (4 - H % 4))
NGEN = 400
CXPB = 1.0
MUTPB = 1.0

# create the reference directions to be used for the optimization
ref_dirs = UniformReferenceDirectionFactory(NOBJ, n_points=H).do()

# create the algorithm object
method = nsga3(pop_size=MU,
               ref_dirs=ref_dirs)

problem = get_problem(PROBLEM, n_var=NDIM, n_obj=NOBJ)
pf = problem.pareto_front(ref_dirs)

# execute the optimization
res = minimize(problem,
               method,
               termination=('n_gen', NGEN))

print(igd(res.F, pf))
print(numpy.min(res.F, axis=0), numpy.max(res.F, axis=0))

# ax = plotting.plot(res.F, show=False, alpha=1.0)
# ax.view_init(45, 45)
# plt.show()