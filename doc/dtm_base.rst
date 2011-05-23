.. _dtm-bases:

=================================
Distributed Task Manager Overview
=================================

DTM is a distributed task manager which works over many communication layers. Currently, all modern MPI implementations are supported through mpi4py, and an experimental TCP backend is available.

Introductory example
====================

First, lets take a look to a very simple distribution example. The sequential program we want to parallelize reads as follow : ::
    
    def op(x):
        return x + 1./x     # Or any operation
        
    if __name__ == "__main__":
        nbrs = range(1, 1000)
        results = map(op, nbrs)
    
This program simply applies an arbitrary operation to each item of a list. Although it is a very trivial program (and therefore would not benefit from a parallelization), lets assume we want to distribute the workload over a cluster.
We just use the DTM parallel version of `map()`, and import correctly the taskmanager. ::
    
    from deap import dtm
    
    def op(x):
        return x + 1./x     # Or any operation
    
    def main():
        nbrs = range(1, 1000)
        results = dtm.map(op, nbrs)
    
    dtm.start(main)
    
And we are done! This program can now run over 2, 4, 7, or 256 processors, without changing anything. The operation done in the op() function can be virtually any operation.

.. note::
    The encapsulation of the main execution code into a function is required by DTM, in order to be able to control which worker will start the execution.

DTM Main Features
=================

DTM has some very interesting features :

- Offers a similar interface to the Python's multiprocessing module
- Automatically balances the load between workers (and therefore supports heterogeous networks and different task durations)
- Supports an arbitrary number of workers without changing a byte in the program
- Abstracts the user from the communication management (the same program can be run over MPI, TCP or multiprocessing just by changing the communication manager)
- Provides easy-to-use parallelization paradigms
- Offers a trace mode, which can be used to tune the performance of the running program (still experimental)


Functions documentation
=======================

.. autoclass:: deap.dtm.taskmanager.DtmControl
    :members:
        
DTM + EAP = DEAP
================

As part of the DEAP framework, EAP offers an easy DTM integration. As the EAP algorithms use a map function stored in the toolbox to spawn the individuals evaluations (by default, this is simply the traditionnal Python map), the parallelization can be made very easily, by replacing the map operator in the toolbox : ::
    
    from deap import dtm
    tools.register("map", dtm.map)
    
Thereafter, ensure that your main code is in enclosed in a Python function (for instance, main), and just add the last line : ::
    
    dtm.start(main)
    
For instance, take a look at the short version of the onemax. This is how it may be parallelized : ::
    
    from deap import dtm
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", array.array, fitness=creator.FitnessMax)

    tools = toolbox.Toolbox()

    # Attribute generator
    tools.register("attr_bool", random.randint, 0, 1)

    # Structure initializers
    tools.register("individual", creator.Individual, "b", toolbox.Repeat(tools.attr_bool, 100))
    tools.register("population", list, toolbox.Repeat(tools.individual, 300))

    def evalOneMax(individual):
        return sum(individual),

    tools.register("evaluate", evalOneMax)
    tools.register("mate", operators.cxTwoPoints)
    tools.register("mutate", operators.mutFlipBit, indpb=0.05)
    tools.register("select", operators.selTournament, tournsize=3)
    tools.register("map", dtm.map)

    stats_t = operators.Stats(lambda ind: ind.fitness.values)
    stats_t.register("Avg", operators.mean)
    stats_t.register("Std", operators.std_dev)
    stats_t.register("Min", min)
    stats_t.register("Max", max)

    def main():
        pop = tools.population()
        hof = operators.HallOfFame(1)
        stats = tools.clone(stats_t)

        algorithms.eaSimple(tools, pop, cxpb=0.5, mutpb=0.2, ngen=40, stats=stats, halloffame=hof)
        logging.info("Best individual is %s, %s", hof[0], hof[0].fitness.values)
        
        return pop, stats, hof

    dtm.start(main)


Troubleshooting
===============


