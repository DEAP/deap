Where to Start?
===============
If your are used to an other evolutionary algorithm framework, you'll notice
we do things differently with DEAP. Instead of limiting you with predefined
types, we provide ways of creating the appropriate ones. Instead of providing
closed initializers, we enable you to customize them as you wish. Instead of
suggesting unfit operators, we explicitly ask you to choose them wisely.
Instead of implementing many sealed algorithms, we allow you to write the one
that fit all your needs. This tutorial will present a quick overview of what
DEAP is all about along of with what every DEAP program is made of.

Types
-----
The first thing to do is to think of the appropriate type for your problem.
As we said above, DEAP enables you to build your own types, this is done with
the :mod:`~deap.creator` module. Creating an appropriate type might seems
overwhelming but the creator makes it very easy. In fact, this is usually done
in a single line. For example, the following creates a :class:`fitness` class
for a minimization problem and an :class:`individual` class that is derived
from a list with a fitness attribute set to the just created fitness.
::

    from deap import base, creator
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

That's it. More on creating types can be found in the :ref:`creating-types`
tutorial.

Initialization
--------------
Once the types are created you need to fill them with sometimes random values,
sometime guessed ones. Again, DEAP provides an easy mechanism to do just that.
The :class:`~deap.base.Toolbox` is a container for tools of all sorts
including initializers that can do what is needed of them. The following takes
on the last lines of code to create the initializers for individuals
containing random floating point numbers and for a population that contains
them.
::

    import random
    from deap import tools
    
    IND_SIZE = 10
    
    toolbox = base.Toolbox()
    toolbox.register("attribute", random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual, 
        toolbox.attribute, n=IND_SIZE)
    toolbox.register("population", tools.initRepeat, toolbox.individual)

This creates functions to initialize populations from individuals that are
themselves initialized with random float numbers. More initialization methods
are found in the :ref:`creating-types` tutorial and the various 
:ref:`examples`.

Operators
---------
Operators are just like initalizers, excepted that some are already
implemented in the :mod:`~deap.tools` module. Once you've chose the perfect
ones simply register them in the toolbox. In addition you must create your
evaluation function. This is how it is done in DEAP.
::

    def evaluate(individual):
        return sum(individual),
    
    toolbox.register("mate", tools.cxTwoPoints)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("evaluate", evaluate)

The registered functions are renamed by the toolbox to allows genericity so
that the algorithm does not depend on operators name. Note also that fitness
values must be iterable, that is why we return tuple in the evaluate function.
More on this in the :ref:`next-step` tutorial and :ref:`examples`.

Algorithms
----------
Now that everything is ready, we can start to write our own algorithm. It is
usually done in a main function. For the purpose of completeness we will
develop the complete generational algorithm.
::

    def main():
        pop = toolbox.population(n=50)
        CXPB, MUTPB, NGEN = 0.5, 0.2, 40
        
        # Evaluate the entire population
        fitnesses = map(toolbox.evaluate, pop)
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
        
        for g in range(NGEN):
            # Select the next generation individuals
            offspring = toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = map(toolbox.clone, offspring)
            
            # Apply crossover and mutation on the offsprings
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values
                    
            for mutant in offsprings:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values
                    
            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
                
            # The population is entirely replaced by the offsprings
            pop[:] = offspring	 

        return pop

There is also the possibility to to use one of the five algorithms readily
available in the :mod:`~deap.algorithms` and :mod:`~deap.cma` modules.