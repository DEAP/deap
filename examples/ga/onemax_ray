#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.


#    example which maximizes the sum of a list of integers
#    each of which can be 0 or 1

import random
import ray
import numpy as np
from ray.util import ActorPool
from deap import base
from deap import creator
from deap import tools
from numpy import linalg as LA


#  specify resources per actor here. Actors function as workers that execute a list of tasks. In this case those tasks
#  will be evaluating the population.
@ray.remote(num_cpus=1, num_gpus=0)
class DeapActor:
    #  Do your eval here instead of in the "eval" function registered in the toolbox
    def eval(self, list_individual: list):
        #  comment/uncomment to do hard math to slow down the evolution and simulate a long-running eval task
        #  increase/decrease array size to make faster/slower
        w, v = LA.eig(5 * np.random.random_sample((100, 100)))
        return sum(list_individual),


creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Attribute generator
#                      define 'attr_bool' to be an attribute ('gene')
#                      which corresponds to integers sampled uniformly
#                      from the range [0,1] (i.e. 0 or 1 with equal
#                      probability)
toolbox.register("attr_bool", random.randint, 0, 1)

# Structure initializers
#                         define 'individual' to be an individual
#                         consisting of 100 'attr_bool' elements ('genes')
toolbox.register("individual", tools.initRepeat, creator.Individual,
                 toolbox.attr_bool, 100)

# define the population to be a list of individuals
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# register some stats
stats = tools.Statistics(key=lambda ind: ind.fitness.values)
stats.register("avg", np.mean)
stats.register("std", np.std)
stats.register("min", np.min)
stats.register("max", np.max)

# logbook
logbook = tools.Logbook()
logbook.header = "gen", "avg", "std", "max", "min"


# the goal ('fitness') function to be maximized
def evalOneMax(actor: DeapActor, individual):  # note signature change (actor, individual)
    #  Don't do your eval here anymore. Instead, call "eval" on the actor.

    # converting the individual into a list, since the remote actor doesn't have an instance of
    # the "Individual" class, so it won't know how to deserialize an individual.
    list_individual = [x for x in individual]
    return actor.eval.remote(list_individual)  # Note tha use of the .remote() function, this is standard Ray syntax


# ----------
# Operator registration
# ----------
# register the goal / fitness function
toolbox.register("evaluate", evalOneMax)

# register the crossover operator
toolbox.register("mate", tools.cxTwoPoint)

# register a mutation operator with a probability to
# flip each attribute/gene of 0.05
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)

# operator for selecting individuals for breeding the next
# generation: each individual of the current generation
# is replaced by the 'fittest' (best) of three individuals
# drawn randomly from the current generation.
toolbox.register("select", tools.selTournament, tournsize=3)


# ----------

def main():
    ray.init()  # start ray
    random.seed(64)

    #  set number of remote actors to use
    num_actors = 4
    actors = []  # list to hold the actors

    # spin up the requested number of actors
    for x in range(num_actors):
        actor = DeapActor.remote()
        actors.append(actor)

    #  create an actor pool from the actors.
    pool = ActorPool(actors)

    # create an initial population of 300 individuals (where
    # each individual is a list of integers)
    pop = toolbox.population(n=300)

    # CXPB  is the probability with which two individuals
    #       are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB, MUTPB = 0.5, 0.2

    print("Start of evolution")

    # Evaluate the entire population
    fitnesses = list(pool.map(toolbox.evaluate, pop))  # actor pool maps eval to pop
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    print("  Evaluated %i individuals" % len(pop))

    # Extracting all the fitnesses of
    fits = [ind.fitness.values[0] for ind in pop]

    # Variable keeping track of the number of generations
    g = 0

    # Begin the evolution
    while max(fits) < 100 and g < 1000:
        # A new generation
        g = g + 1

        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):

            # cross two individuals with probability CXPB
            if random.random() < CXPB:
                toolbox.mate(child1, child2)

                # fitness values of the children
                # must be recalculated later
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:

            # mutate an individual with probability MUTPB
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = list(pool.map(toolbox.evaluate, invalid_ind))  # actor pool maps eval function to pop
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # print("  Evaluated %i individuals" % len(invalid_ind))

        # The population is entirely replaced by the offspring
        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]

        record = stats.compile(pop)
        logbook.record(gen=g, **record)
        print(logbook.stream)

    print("-- End of (successful) evolution --")

    best_ind = tools.selBest(pop, 1)[0]
    print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))


if __name__ == "__main__":
    main()
