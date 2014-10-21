=============
Checkpointing
=============
In this tutorial, we will present how persistence can be achieved in your
evolutions. The only required tools are a simple :class:`dict` and a
serialization method. Important data will be inserted in the dictionary and
serialized to a file so that if something goes wrong, the evolution can be
restored from the last saved checkpoint. It can also serve to continue an
evolution beyond the pre-fixed termination criterion.

Checkpointing is not offered in standard algorithms such as eaSimple,
eaMuPlus/CommaLambda and eaGenerateUpdate. You must create your own algorithm
(or copy an existing one) and introduce this feature yourself.

Starting with a very basic example, we will cover the necessary stuff to
checkpoint everything needed to restore an evolution. We skip the class
definition and registration of tools in the toolbox to go directly to the
algorithm and the main function. Our main function receives an optional string
argument containing the path of the checkpoint file to restore. ::

    import pickle
    
    def main(checkpoint=None):
        if checkpoint:
            # A file name has been given, then load the data from the file
            with open(checkpoint, "r") as cp_file:
                cp = pickle.load(cp_file)
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

                with open("checkpoint_name.pkl", "wb") as cp_file:
                    pickle.dump(cp, cp_file)

Now, the whole data will be written in a pickled dictionary every *FREQ*
generations. Loading the checkpoint is done if the main function is given a path
to a checkpoint file. In that case, the evolution continues from where it was in
the last checkpoint. It will produce the exact same results as if it was not
stopped and reloaded because we also restored the random module state. If you
use numpy's random numbers, don't forget to save and reload their state too.
