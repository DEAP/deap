.. _ga-onemax:

=========================
One Max Genetic Algorithm
=========================

This is the first complete program built with EAP. It will help new users to overview some of the possibilities in EAP. The problem is very simple, we search for a :data:`1` filled list individual. This problem is widely used in the evolutionary computation community since it is very simple and it illutrates well the potential of evolutionary algorithms.

Setting Things Up
=================

Here we use the one max problem to show how simple can be an evolutionary algorithm with EAP. The first thing to do is to ellaborate the structures of the algorithm. It is pretty obvious in this case that an individual that can contain a serie of `booleans` is the most interesting kind of structure available. EAP does not contain any explicit individual structure since it is simply a container of attributes associated with a fitness. Instead, it provides a convenient method for creating types called the creator.

-------
Creator
-------

The creator is a class factory that can build at runtime new classes that inherit from base classes. It is very useful since an individual can be any type of container from list to n-ary tree. The creator allows to bind those base classes together in order to build more complex new structures convenient for evolutionary computation.

Let see an example of how to use the creator to setup an individual that contains an array of booleans and a miximizing fitness. We will first need to import the :mod:`eap.base` and :mod:`eap.creator` modules. The :mod:`eap.base` module contains the basic structure such as List, Array and Tree.

The creator defines at first a single function called :func:`~eap.creator.create` that is used to create types. The :func:`~eap.creator.create` function takes at least 2 arguments plus one optional argument. The first argument *name* is the actual name of the type that we want to create, here it is :class:`Individual`. The second argument *bases* is a tuple of base classes that the new type created should inherit from. Finaly the optional argument *dict* is a dictionary of members to add to the new type (this subject is more detailed in the documentation, and out of the current scope). ::

    creator.create("FitnessMax", (base.Fitness), {"weights" : (1,0)})
    creator.create("Individual", (base.Array,), {"fitness" : creator.FitnessMax})
    creator.create("Population", (base.List,))

The first line creates a maximizing fitness by replacing in the base type :class:`~eap.base.Fitness` the weights member with (1.0,) that means to maximize this fitness. The second line creates an :class:`Individual` class that inherits the properties of an :class:`~eap.base.Array` and has a :attr:`fitness` member of the type :class:`FitnessMax` that was just created. The third line creates a :class:`Population` class that is simply a :class:`~eap.base.List`. The three lines are exactly the same as the following bunch of code ::

    class FitnessMax(base.Fitness):
        weights = (1.0,)

    class Individual(base.Array):
        def __init__(self, typecode, size, content):
            base.Array.__init__(self, typecode, size, content)
            self.fitness = FitnessMax()
    
    class Population(base.List):
        def __init__(self, size, content):
            base.List.__init__(self, size, content)

-------
Toolbox
-------

The :mod:`eap.toolbox` is an other convenience module that contains a :class:`~eap.toolbox.Toolbox` class intended store functions with their arguments. The :class:`~eap.toolbox.Toolbox` contains two simple methods, :meth:`~eap.toolbox.Toolbox.register` and :meth:`~eap.toolbox.Toolbox.unregister`.::

    tools = toolbox.Toolbox()
    tools.register("individual", creator.Individual, size=100, typecode="b",
            content=lambda: random.randint(0, 1))
    tools.register("population", creator.Population, size=300,
            content=tools.individual)


The two last lines of code create two functions within the toolbox, the first that instaciates individuals and the second that instanciate populations.

The Evaluation Function
=======================

The evaluation function is pretty simple in this case, we need to count the number of :data:`1` in the individual and append this value to the fitness. This is done by the following lines of code. ::
    
    def evalOneMax(individual):
        if not individual.mFitness.isValid():
            individual.mFitness.append(sum(individual))
   
The Genetic Operators
=====================

There is two way of using operators, the first one, is to simply call the function from the :mod:`~eap.toolbox` module and the second one is to register them with their argument in the a :class:`~eap.toolbox.Toolbox`. The most convenient way is to register them in the toolbox, because it allows to easily switch between operators if desired. The toolbox method is also used in the algorithms `one max short version <http://doc.deap.googlecode.com/hg/short_ga_onemax.html one max short version>`_.

Registering the operators and their default arguments in the toolbox is done as follow. ::

    lTools.register('evaluate', evalOneMax)
    lTools.register('mate', toolbox.twoPointsCx)
    lTools.register('mutate', toolbox.flipBitMut, indpb=0.05)
    lTools.register('select', toolbox.tournSel, tournsize=3)

Evolving the Population
=======================

-----------------------
Creating the Population
-----------------------

Before evolving it, we need to instanciate a population. This step is done effortless using the method we registered in the :class:`~eap.toolbox.Toolbox`. ::

    pop = tools.population()

-----------------------
The Appeal of Evolution
-----------------------

The evolution of the population is the last thing to do before getting results. In this example we **do not** use the :mod:`eap.algorithm` module in order to show how to manipulate the different features of EAP. Let say that we want to evolve fo a fixed number of generation (:data:`MAXGEN`), the evolution will then begin with a simple for statement. ::

    for g in range(MAXGEN):
        evolve...

Is that simple enough? Lets continue with more complicated things, mating and mutating the population. The crossover and mutation operators provided with eap usualy take respectivly 2 and 1 individual(s) on input and return 2 and 1 *new* individual(s). The simple GA algorithme states that the produced individuals shall replace their parents in the population, this is what is done by the following lines of code, where a crossover is applied with probability :data:`CXPB` and a mutation with probability :data:`MUTPB`. ::

        for i in range(1, len(pop), 2):
            if random.random() < CXPB:
                pop[i - 1], pop[i] = tools.mate(pop[i - 1], pop[i])
    
        for i in range(len(pop)):
            if random.random() < MUTPB:
                pop[i] = tools.mutate(pop[i])

The population now needs to be evaluated, we use the map operator in order to apply the evaluation on every individual of the population. ::

    map(tools.evaluate, pop)

And finaly, last but not least, the selection part occurs. We replace the whole population by individuals selected by tournament (as defined in the toolbox) in that same population. ::

    pop[:] = tools.select(pop, n=len(pop))

The ``[:]`` needs to be used in order to replace the slice of objects with the new list of individuals and not the whole population object that would lose its :class:`Population` type (this would not be very problematic anyway).

Some statistics may be gathered on the population, the following lines print the min, max, mean and standard deviation of the population. ::

    fits = [ind.fitness[0] for ind in pop]
    print '  Min %f' % min(fits)
    print '  Max %f' % max(fits)
    lenght = len(pop)
    mean = sum(fits) / lenght
    sum2 = sum(map(lambda x: x**2, fits))
    std_dev = (sum2 / lenght - mean**2)**0.5
    print '  Mean %f' % (mean)
    print '  Std. Dev. %f' % std_dev

The complete `One Max Genetic Algorithm <http://eap.deap.googlecode.com/hg/src/examples/ga_onemax.py>`_ code.