from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt

try:
    import numpy as np
except:
    exit()

import random
rnd = random.Random()
rnd.seed(128)

from deap.benchmarks import movingpeaks

sc = movingpeaks.SCENARIO_1
sc["uniform_height"] = 0
sc["uniform_width"] = 0

mp = movingpeaks.MovingPeaks(dim=2, random=rnd, **sc)

fig = plt.figure()
ax = Axes3D(fig)
X = np.arange(0, 100, 1.0)
Y = np.arange(0, 100, 1.0)
X, Y = np.meshgrid(X, Y)
Z = np.fromiter(map(lambda x: mp(x)[0], zip(X.flat,Y.flat)), dtype=np.float, count=X.shape[0]*X.shape[1]).reshape(X.shape)

ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.jet, linewidth=0.2)

plt.xlabel("x")
plt.ylabel("y")

plt.show()