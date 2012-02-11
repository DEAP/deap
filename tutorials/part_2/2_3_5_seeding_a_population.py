# 2.3.5 Seeding a population
import json

from deap import base
from deap import creator

creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))
creator.create("Individual", list, fitness=creator.FitnessMax)

def initIndividual(icls, content):
    return icls(content)

def initPopulation(pcls, ind_init, filename):
    contents = json.load(open(filename, "r"))
    return pcls(ind_init(c) for c in contents)

toolbox = base.Toolbox()

toolbox.register("individual_guess", initIndividual, creator.Individual)
toolbox.register("population_guess", initPopulation, list, toolbox.individual_guess, "my_guess.json")

population = toolbox.population_guess()
