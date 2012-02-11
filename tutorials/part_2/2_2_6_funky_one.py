## 2.2.6 Funky one
import random

from deap import base
from deap import creator
from deap import tools

creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

INT_MIN, INT_MAX = 5, 10
FLT_MIN, FLT_MAX = -0.2, 0.8
N_CYCLES = 4

toolbox.register("attr_int", random.randint, INT_MIN, INT_MAX)
toolbox.register("attr_flt", random.uniform, FLT_MIN, FLT_MAX)
toolbox.register("individual", tools.initCycle, creator.Individual,
                 (toolbox.attr_int, toolbox.attr_flt), n=N_CYCLES)
