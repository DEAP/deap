from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt

try:
    import numpy as np
except:
    exit()

from deap import benchmarks

def untuple(sol):
    return benchmarks.himmelblau(sol)[0]

fig = plt.figure()
ax = Axes3D(fig, azim = -29, elev = 49)
X = np.arange(-6, 6, 0.1)
Y = np.arange(-6, 6, 0.1)
X, Y = np.meshgrid(X, Y)
Z = np.array(map(untuple, zip(X,Y)))

ax.plot_surface(X, Y, Z, rstride=1, cstride=1, norm=LogNorm(), cmap=cm.jet, linewidth=0.2)
 
plt.xlabel("x")
plt.ylabel("y")

plt.show()