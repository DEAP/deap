import pickle

from deap import tools

from stats import record

logbook = tools.Logbook()
logbook.record(gen=0, evals=30, **record)

print(logbook)

gen, avg = logbook.select("gen", "avg")

with open("logbook.pkl", "w") as lb_file:
	pickle.dump(logbook, lb_file)

# Cleaning the pickle file ...
import os
os.remove("logbook.pkl")

logbook.header = "gen", "avg", "spam"
print(logbook)

print(logbook.stream)
logbook.record(gen=1, evals=15, **record)
print(logbook.stream)

from multistats import record

logbook = tools.Logbook()
logbook.record(gen=0, evals=30, **record)

logbook.header = "gen", "evals", "fitness", "size"
logbook.chapters["fitness"].header = "min", "avg", "max"
logbook.chapters["size"].header = "min", "avg", "max"

print(logbook)

gen = logbook.select("gen")
fit_mins = logbook.chapters["fitness"].select("min")
size_avgs = logbook.chapters["size"].select("avg")

import matplotlib.pyplot as plt

fig, ax1 = plt.subplots()
line1 = ax1.plot(gen, fit_mins, "b-", label="Minimum Fitness")
ax1.set_xlabel("Generation")
ax1.set_ylabel("Fitness", color="b")
for tl in ax1.get_yticklabels():
    tl.set_color("b")

ax2 = ax1.twinx()
line2 = ax2.plot(gen, size_avgs, "r-", label="Average Size")
ax2.set_ylabel("Size", color="r")
for tl in ax2.get_yticklabels():
    tl.set_color("r")

lns = line1 + line2
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc="center right")

plt.show()