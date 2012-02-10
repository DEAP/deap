## 2.1 Fitness
from deap import base
from deap import creator

## FitnessMin
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

## FitnessMulti
creator.create("FitnessMulti", base.Fitness, weights=(-1.0, 1.0))
