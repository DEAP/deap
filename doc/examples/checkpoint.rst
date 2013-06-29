=============
Checkpointing
=============

This example will cover how to checkpoint important data during an evolution
to restart when something goes wrong or even after a termination criterion has
been met. Checkpointing is not offered in standard algorithm such as eaSimple,
eaMuPlus/CommaLambda, and eaGenerateUpdate. You must create your own algorithm
as in the onemax example or use variation to shorten things up.

Starting with a very basic example we will add the necessary  stuff to
checkpoint everything needed to restart an evolution. We will skip the
creation of classe and registration of tools in the toolbox to go directly to
the algorithm and the main function. Our main function will receive a string
of the checkpoint path if desired. ::

    import pickle
    
    def main(checkpoint=None):
        if checkpoint:
            cp = pickle.load(open(checkpoint, "r"))
            population = cp["population"]
            start_gen = cp["generation"]
            halloffame = cp["halloffame"]
            logbook = cp["logbook"]
            random.setstate(cp["rndstate"])
        else:
            population = toolbox.population(n=300)
            start_gen = 0
            halloffame = tools.HallOfFame(maxsize=1)
            logbook = tools.Logbook()

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)

        for gen in range(start_gen, NGEN):
            population = algorithms.varAnd(population, toolbox, cxpb=CXPB, mutpb=MUTPB)

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in population if not ind.fitness.valid]
            fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            halloffame.update(population)
            record = stats.compile(population)
            logbook.record(gen=gen, evals=len(invalid_ind), **record)

            population = toolbox.select(population, k=len(population))

            if gen % FREQ ==0:
                cp = dict(population=population, generation=gen, halloffame=halloffame,
                          logbook=logbook, rndstate=random.getstate())
                pickle.dump(cp, open("checkpoint_name.pkl", "w"))

That's it, the whole data will be written in a pickled dictionary at every
*FREQ* generation. Loading the checkpoint is done if the main function is
given a path. The evolution restarts from where it was in the last checkpoint
and will produce the exact same results as if it was not stopped and reloaded
because of the state of the random module. If you use numpy random numbers
don't forget to save and reload its state too.
