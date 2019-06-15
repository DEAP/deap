import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from deap import tools

NOBJ = 3
P = 12

fig = plt.figure(figsize=(7, 7))
ax = fig.add_subplot(111, projection="3d")

# the coordinate origin (black + sign)
ax.scatter(0, 0, 0, c="k", marker="+", s=100)

# reference points (gray)
ref_points = tools.uniform_reference_points(NOBJ, P)

ax.scatter(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], marker="o", s=48)

# final figure details
ax.set_xlabel("$f_1(\mathbf{x})$", fontsize=15)
ax.set_ylabel("$f_2(\mathbf{x})$", fontsize=15)
ax.set_zlabel("$f_3(\mathbf{x})$", fontsize=15)
ax.view_init(elev=11, azim=-25)
ax.autoscale(tight=True)
plt.tight_layout()

plt.show()
