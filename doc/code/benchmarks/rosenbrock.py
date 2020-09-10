from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt

try:
    import numpy as np
except:
    exit()

from deap import benchmarks

def rosenbrock_arg0(sol):
    return benchmarks.rosenbrock(sol)[0]

fig = plt.figure()
# ax = Axes3D(fig, azim = -29, elev = 50)
ax = Axes3D(fig)
X = np.arange(-2, 2, 0.1)
Y = np.arange(-1, 3, 0.1)
X, Y = np.meshgrid(X, Y)
Z = np.fromiter(list(map(rosenbrock_arg0, list(zip(X.flat,Y.flat)))), dtype=np.float, count=X.shape[0]*X.shape[1]).reshape(X.shape)

ax.plot_surface(X, Y, Z, rstride=1, cstride=1,  norm=LogNorm(), cmap=cm.jet, linewidth=0.2)
 
plt.xlabel("x")
plt.ylabel("y")

plt.show()