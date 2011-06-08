.. _symbreg:
    
========================================================
A Genetic Programming Introduction : Symbolic Regression
========================================================

Symbolic regression is one of the best known problems in GP (see :ref:`refPapersSymbreg`). It is commonly used as a tuning problem for new algorithms, but is also widely used with real-life distributions, where other regression methods may not work. It is conceptually a simple problem, and therefore makes a good introductory example for the GP framework in DEAP.

All symbolic regression problems use an arbitrary data distribution, and try to fit the most accurately the data with a symbolic formula. Usually, a measure like the RMSE (Root Mean Square Error) is used to measure an individual's fitness.

In this example, we use a classical distribution, the quartic polynomial :math:`(x^4 + x^3 + x^2 + x)`, a one-dimension distribution. *20* equidistant points are generated in the range [-1, 1], and are used to evaluate the fitness.


Creating the primitives set
===========================

One of the most crucial aspect of a GP program is the choice of the primitives set. They should make good building blocks for the individuals so the evolution can succeed. In this problem, we use a classical set of primitives, which are basic arithmetic functions : ::
    
    def safeDiv(left, right):
        try:
            return left / right
        except ZeroDivisionError:
            return 0

    pset = gp.PrimitiveSet("MAIN", 1)
    pset.addPrimitive(operator.add, 2)
    pset.addPrimitive(operator.sub, 2)
    pset.addPrimitive(operator.mul, 2)
    pset.addPrimitive(safeDiv, 2)
    pset.addPrimitive(operator.neg, 1)
    pset.addPrimitive(math.cos, 1)
    pset.addPrimitive(math.sin, 1)
    pset.addEphemeralConstant(lambda: random.randint(-1,1))
    
The redefinition of the division is made to protect it against a zero division error (which would crash the program). The other functions are simply a mapping from the Python :mod:`operator` module. The number following the function is the *arity* of the primitive, that is the number of entries it takes (this will be used by DTM to build the individuals from the primitives).

On the last line, we declare an *ephemeral constant*. This is a special terminal type, which does not have a fixed value. When the program appends an ephemeral constant terminal to a tree, the function it contains is executed, and its result is inserted as a constant terminal. In this case, those constant terminals can take the values -1, 0 or 1.

The second argument of :class:`~deap.gp.PrimitiveSet` is the number of inputs. Here, as we have only a one dimension regression problem, there is only one input, but it could have as many as you want. By default, those inputs are named "ARGx", where "x" is a number, but you can easily rename them : ::
    
    pset.renameArguments({"ARG0" : "x"})

Creator
=======

As any evolutionary program, symbolic regression needs (at least) two object types : an individual containing the genotype and a fitness. We can easily create them with the creator : ::
    
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin, pset=pset)

The first line creates the fitness object (this is a minimization problem, so the weight is negative). The `weights` argument must be an iterable of weights, even if there is only one fitness measure. The second line create the individual object itself. Very straightforward, we can see that it will be based upon a tree, to which we add two attributes : a fitness and the primitive set. If, for any reason, the user would want to add any other attribute (for instance, a file in which the individual will be saved), it would be as easy as adding this attribute of any type to this line. After this declaration, any individual produced will contain those wanted attributes.
    

Toolbox
=======

Now, we want to register some parameters specific to the evolution process. In DEAP, this is done through the toolbox : ::
    
    toolbox = base.Toolbox()
    toolbox.register("expr", gp.genRamped, pset=pset, min_=1, max_=2)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("lambdify", gp.lambdify, pset=pset)

    def evalSymbReg(individual):
        # Transform the tree expression in a callable function
        func = toolbox.lambdify(expr=individual)
        # Evaluate the sum of squared difference between the expression
        # and the real function : x**4 + x**3 + x**2 + x
        values = (x/10. for x in xrange(-10,10))
        diff_func = lambda x: (func(x)-(x**4 + x**3 + x**2 + x))**2
        diff = sum(map(diff_func, values))
        return diff,

    toolbox.register("evaluate", evalSymbReg)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("mate", gp.cxUniformOnePoint)
    toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
    toolbox.register('mutate', gp.mutUniform, expr=toolbox.expr_mut)

First, a toolbox instance is created (in some problem types like coevolution, you may consider creating more than one toolbox). Then, we can register any parameters. The first lines register how to create an individual (by calling gp.genRamped with the previously defined primitive set), and how to create the population (by repeating the individual initialization).

We may now introduce the evaluation function, which will receive an individual as input, and return the corresponding fitness. This function uses the `lambdify` function previously defined to transform the individual into its executable form -- that is, a program. After that, the evaluation is only simple maths, where the difference between the values produced by the evaluated individual and the real values are squared and summed to compute the RMSE, which is returned as the fitness of the individual.

.. warning::
    Even if the fitness only contains one measure, keep in mind that DEAP stores it as an iterable. Knowing that, you can understand why the evaluation function must return a tuple value (even if it is a 1-tuple) : ::
        
        return diff,
        
    Returning only the value would produce strange behaviors and errors, as the selection and stats functions relies on the fact that the fitness is always an iterable.

Afterwards, we register the evaluation function. We also choose the selection method (a tournament of size 3), the mate method (one point crossover with uniform probability over all the nodes), the mutation method (an uniform probability mutation which may append a new full sub-tree to a node).

At this point, any structure with an access to the toolbox instance will also have access to all of those registered parameters. Of course, the user could register other parameters basing on his needs.


Statistics
==========

Although optional, statistics are often useful in evolutionary programming. DEAP offers a simple class which can handle most of the "boring work". In this case, we want to keep four measures over the fitness distribution : the mean, the standard deviation, the minimum and the maximum. ::
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("Avg", tools.mean)
    stats.register("Std", tools.std)
    stats.register("Min", min)
    stats.register("Max", max)
    

Launching the evolution
=======================

At this point, DEAP has all the information needed to begin the evolutionary process, but nothing has been initialized. We can start the evolution by creating the population and then call a pre-made algorithm, as eaSimple : ::

    def main():
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("Avg", tools.mean)
        stats.register("Std", tools.std)
        stats.register("Min", min)
        stats.register("Max", max)
        
        pop = toolbox.population(n=300)         # Population length
        hof = tools.HallOfFame(1)
        
        algorithms.eaSimple(toolbox, pop, 0.5, 0.1, 40, stats, halloffame=hof)
        logging.info("Best individual is %s, %s", gp.evaluate(hof[0]), hof[0].fitness)
        
        return pop, stats, hof

    if __name__ == "__main__":
        main()

The hall of fame is a specific structure which contains the *n* best individuals (here, the best one only). The first line set up the Python logger used by DEAP to provide information, warnings or errors about the evolution. Its level can be adjusted according to the desired verbosity level (see :mod:`logging`).

Complete Example
================

.. literalinclude:: ../examples/gp_symbreg.py
    :lines: 21-
    

.. _refPapersSymbreg:

Reference
=========

*John R. Koza, "Genetic Programming: On the Programming of Computers by Means of Natural Selection", MIT Press, 1992, pages 162-169.*