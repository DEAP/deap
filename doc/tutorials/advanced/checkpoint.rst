=============
Checkpointing
=============
In this tutorial we will present how persistance can be acheived. The only required
tools are a simple :class:`dict` and a serialization method. Important data will
be inserted in the diction and serialized to a file so that if something goes wrong
the evolution can be restarted from the last saved checkpoint. It can also serve
to continue an evolution beyond the pre-fixed termination criterion.

Checkpointing is not offered in standard algorithm such as eaSimple,
eaMuPlus/CommaLambda, and eaGenerateUpdate. You must create your own algorithm
(or copy an existing one) and intriduce this feature yourself.

Starting with a very basic example we will cover the necessary stuff to
checkpoint everything needed to restart an evolution. We will skip the
creation of classe and registration of tools in the toolbox to go directly to
the algorithm and the main function. Our main function will receive a string
of the checkpoint path if desired. ::

    import pickle
    
    def main(checkpoint=None):
        if checkpoint:
            # A file name has been given, then load the data from the file
            cp = pickle.load(open(checkpoint, "r"))
            population = cp["population"]
            start_gen = cp["generation"]
            halloffame = cp["halloffame"]
            logbook = cp["logbook"]
            random.setstate(cp["rndstate"])
        else:
            # Start a new evolution
            population = toolbox.population(n=300)
            start_gen = 0
            halloffame = tools.HallOfFame(maxsize=1)
            logbook = tools.Logbook()

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean)
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

            if gen % FREQ == 0:
                # Fill the dictionary using the dict(key=value[, ...]) constructor
                cp = dict(population=population, generation=gen, halloffame=halloffame,
                          logbook=logbook, rndstate=random.getstate())
                pickle.dump(cp, open("checkpoint_name.pkl", "w"))

Now, the whole data will be written in a pickled dictionary every *FREQ*
generations. Loading the checkpoint is done if the main function is given a
path to a checkpoint file. In that case, the evolution restarts from where it
was in the last checkpoint. It will produce the exact same results as if it
was not stopped and reloaded because of the random module state . If you use
numpy random numbers don't forget to save and reload its state too.
