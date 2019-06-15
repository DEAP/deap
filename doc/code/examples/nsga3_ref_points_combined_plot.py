import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy

from deap import tools

NOBJ = 3
P = [2, 1]
SCALES = [1, 0.5]

fig = plt.figure(figsize=(7, 7))
ax = fig.add_subplot(111, projection="3d")

# the coordinate origin
ax.scatter(0, 0, 0, c="k", marker="+", s=100)

# reference points
# Parameters
NOBJ = 3
P = [2, 1]
SCALES = [1, 0.5]

# Create, combine and removed duplicates
ref_points = [tools.uniform_reference_points(NOBJ, p, s) for p, s in zip(P, SCALES)]
# ref_points = numpy.concatenate(ref_points, axis=0)
# _, uniques = numpy.unique(ref_points, axis=0, return_index=True)
# ref_points = ref_points[uniques]
##

for subset, p, s in zip(ref_points, P, SCALES):
    ax.scatter(subset[:, 0], subset[:, 1], subset[:, 2], marker="o", s=48, label="p = {}, scale = {}".format(p, s))

# final figure details
ax.set_xlabel("$f_1(\mathbf{x})$", fontsize=15)
ax.set_ylabel("$f_2(\mathbf{x})$", fontsize=15)
ax.set_zlabel("$f_3(\mathbf{x})$", fontsize=15)
ax.view_init(elev=11, azim=-25)
ax.autoscale(tight=True)
plt.legend()
plt.tight_layout()

plt.show()
