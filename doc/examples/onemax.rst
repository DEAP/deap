.. _ga-onemax:

=========================
One Max Genetic Algorithm
=========================

This is the first complete program built with DEAP. It will help new users to
overview some of the possibilities in DEAP. The problem is very simple, we
search for a :data:`1` filled list individual. This problem is widely used in
the evolutionary computation community since it is very simple and it
illutrates well the potential of evolutionary algorithms.

Setting Things Up
=================

Here we use the one max problem to show how simple can be an evolutionary
algorithm with DEAP. The first thing to do is to elaborate the structures of
the algorithm. It is pretty obvious in this case that an individual that can
contain a series of `booleans` is the most interesting kind of structure
available. DEAP does not contain any explicit individual structure since it is
simply a container of attributes associated with a fitness. Instead, it
provides a convenient method for creating types called the creator.

-------
Creator
-------

The creator is a class factory that can build at run-time new classes that
inherit from base classes. It is very useful since an individual can be any
type of container from list to n-ary tree. The creator allows to bind those
base classes together in order to build more complex new structures convenient
for evolutionary computation.

Let see an example of how to use the creator to setup an individual that
contains an array of booleans and a maximizing fitness. We will first need to
import the :mod:`deap.base` and :mod:`deap.creator` modules. The :mod:`deap.base`
module contains the basic structure such as List, Array and Tree.

The creator defines at first a single function called
:func:`~deap.creator.create` that is used to create types. The
:func:`~deap.creator.create` function takes at least 2 arguments plus one
optional argument. The first argument *name* is the actual name of the type
that we want to create, here it is :class:`Individual`. The second argument
*base* is the base classes that the new type created should inherit from.
Finally the optional argument *dict* is a dictionary of members to add to the
new type (this subject is more detailed in the documentation, and out of the
current scope). 
::

    creator.create("FitnessMax", base.Fitness, weights=(1,0))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    creator.create("Population", list)

The first line creates a maximizing fitness by replacing in the base type
:class:`~deap.base.Fitness` the weights member with (1.0,) that means to
maximize this fitness. The second line creates an :class:`Individual` class
that inherits the properties of :class:`list` and has a :attr:`fitness` member
of the type :class:`FitnessMax` that was just created. The third line creates
a :class:`Population` class that is simply a :class:`list`.

-------
Toolbox
-------

The :mod:`deap.toolbox` is an other convenience module that contains a
:class:`~deap.toolbox.Toolbox` class intended store functions with their
arguments. The :class:`~deap.toolbox.Toolbox` contains two simple methods,
:meth:`~deap.toolbox.Toolbox.register` and
:meth:`~deap.toolbox.Toolbox.unregister`. 
::

	toolbox = base.Toolbox()
	
	# Attribute generator
	toolbox.register("attr_bool", random.randint, 0, 1)
	
	# Structure initializers
	toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, 100)
	toolbox.register("population", tools.initRepeat, list, toolbox.individual)


The two last lines of code create two functions within the toolbox, the first
function registered, when called, will instantiate individuals and the second
will instantiate populations.

The Evaluation Function
=======================

The evaluation function is pretty simple in this case, we need to count the
number of ones in the individual. This is done by the
following lines of code. 
::
    
    def evalOneMax(individual):
        return sum(individual),
   
The Genetic Operators
=====================

There is two way of using operators, the first one, is to simply call the
function from the :mod:`~deap.toolbox` module and the second one is to register
them with their argument in the a :class:`~deap.toolbox.Toolbox`. The most
convenient way is to register them in the toolbox, because it allows to easily
switch between operators if desired. The toolbox method is also used in the
algorithms, see the `one max short version
<http://doc.deap.googlecode.com/hg/short_ga_onemax.html one max short
version>`_.

Registering the operators and their default arguments in the toolbox is done
as follow. 
::

    toolbox.register("evaluate", evalOneMax)
    toolbox.register("mate", tools.cxTwoPoints)
    toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

Evolving the Population
=======================

-----------------------
Creating the Population
-----------------------

Before evolving it, we need to instantiate a population. This step is done
effortless using the method we registered in the
:class:`~deap.toolbox.Toolbox`. 
::

    pop = toolbox.population()

-----------------------
The Appeal of Evolution
-----------------------

The evolution of the population is the last thing to do before getting
results. In this example we **do not** use the :mod:`deap.algorithms` module in
order to show how to manipulate the different features of DEAP. Let say that we
want to evolve for a fixed number of generation :data:`MAXGEN`, the evolution
will then begin with a simple for statement. 
::

    for g in range(MAXGEN):
        evolve...

Is that simple enough? Lets continue with more complicated things, mating and
mutating the population. The crossover and mutation operators provided with
deap usually take respectively 2 and 1 individual(s) on input and return 2 and
1 *new* individual(s). The simple GA algorithm states that the produced
individuals shall replace their parents in the population, this is what is
done by the following lines of code, where a crossover is applied with
probability :data:`CXPB` and a mutation with probability :data:`MUTPB`. The 
del statement simply invalidate the fitness of the modified individuals.
::

	# Apply crossover and mutation on the offsprings
	for child1, child2 in zip(offsprings[::2], offsprings[1::2]):
	    if random.random() < CXPB:
	        toolbox.mate(child1, child2)
	        del child1.fitness.values
	        del child2.fitness.values

	for mutant in offsprings:
	    if random.random() < MUTPB:
	        toolbox.mutate(mutant)
	        del mutant.fitness.values

The population now needs to be evaluated, we then apply the evaluation on
every individual in the population that has an invalid fitness. 
::

	# Evaluate the individuals with an invalid fitness
	invalid_ind = [ind for ind in offsprings if not ind.fitness.valid]
	fitnesses = map(toolbox.evaluate, invalid_ind)
	for ind, fit in zip(invalid_ind, fitnesses):
	    ind.fitness.values = fit

And finally, last but not least, the selection part occurs. We replace the
whole population by individuals selected by tournament (as defined in the
toolbox) in that same population. The chosen individuals are duplicated 
according to the :meth:`clone` operator of the toolbox.
::

    pop[:] = [toolbox.clone(ind) for ind in toolbox.select(pop, n=len(pop))]

The ``[:]`` needs to be used in order to replace the slice of objects with the
new list of individuals and not the whole population object that would lose
its :class:`Population` type. This would not be very problematic anyway as
a population is only a :class:`list`.

Some statistics may be gathered on the population, the following lines print
the min, max, mean and standard deviation of the population. ::

	# Gather all the fitnesses in one list and print the stats
	fits = [ind.fitness.values[0] for ind in pop]

	length = len(pop)
	mean = sum(fits) / length
	sum2 = sum(x*x for x in fits)
	std = abs(sum2 / length - mean**2)**0.5

	print "  Min %s" % min(fits)
	print "  Max %s" % max(fits)
	print "  Avg %s" % mean
	print "  Std %s" % std

The complete `One Max Genetic Algorithm
<http://deap.googlecode.com/hg/examples/ga_onemax.py>`_ code is available. It
may be a little different but it does the overall same thing.