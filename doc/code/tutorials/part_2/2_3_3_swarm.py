## 2.2.6 Particle
import random

from deap import base
from deap import creator
from deap import tools

creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))
creator.create("Particle", list, fitness=creator.FitnessMax, speed=None,
               smin=None, smax=None, best=None)
creator.create("Swarm", list, gbest=None, gbestfit=creator.FitnessMax)

def initParticle(pcls, size, pmin, pmax, smin, smax):
    part = pcls(random.uniform(pmin, pmax) for _ in range(size))
    part.speed = [random.uniform(smin, smax) for _ in range(size)]
    part.smin = smin
    part.smax = smax
    return part

toolbox = base.Toolbox()
toolbox.register("particle", initParticle, creator.Particle, size=2,
                 pmin=-6, pmax=6, smin=-3, smax=3)
toolbox.register("swarm", tools.initRepeat, creator.Swarm, toolbox.particle)
