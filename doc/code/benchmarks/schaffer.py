from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt

try:
    import numpy as np
except:
    exit()

from deap import benchmarks

def schaffer_arg0(sol):
    return benchmarks.schaffer(sol)[0]

fig = plt.figure()
ax = Axes3D(fig, azim = -29, elev = 60)
# ax = Axes3D(fig)
X = np.arange(-25, 25, 0.25)
Y = np.arange(-25, 25, 0.25)
X, Y = np.meshgrid(X, Y)
Z = np.zeros(X.shape)

for i in xrange(X.shape[0]):
    for j in xrange(X.shape[1]):
        Z[i,j] = schaffer_arg0((X[i,j],Y[i,j]))

ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet, linewidth=0.2)
 
plt.xlabel("x")
plt.ylabel("y")

plt.show()