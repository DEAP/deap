from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt

try:
    import numpy as np
except:
    exit()

from deap import benchmarks

X = np.arange(-5, 5, 0.1)
Y = np.arange(-5, 5, 0.1)
X, Y = np.meshgrid(X, Y)
Z1 = np.zeros(X.shape)
Z2 = np.zeros(X.shape)

for i in range(X.shape[0]):
    for j in range(X.shape[1]):
        Z1[i,j],  Z2[i,j] = benchmarks.kursawe((X[i,j],Y[i,j]))
        
fig = plt.figure(figsize=(12,5))

ax = fig.add_subplot(1, 2, 1, projection='3d')
ax.plot_surface(X, Y, Z1, rstride=1, cstride=1, cmap=cm.jet, linewidth=0.2)
plt.xlabel("x")
plt.ylabel("y")

ax = fig.add_subplot(1, 2, 2, projection='3d')
ax.plot_surface(X, Y, Z2, rstride=1, cstride=1, cmap=cm.jet, linewidth=0.2)
plt.xlabel("x")
plt.ylabel("y")

plt.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
plt.show()