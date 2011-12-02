.. _creating-types:

Creating Types
==============
This tutorial shows how types are created using the creator and initialized using the toolbox.

Fitness
-------
The provided :class:`~deap.base.Fitness` class is an abstract class that needs
a :attr:`~deap.base.Fitness.weights` attribute in order to be functional. A
minimizing fitness is built using negatives weights, while a maximizing
fitness has positive weights. For example, the following line creates, in the
:mod:`~deap.creator`, a ready to use single objective minimizing fitness named
:class:`FitnessMin`. ::

   creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
   
The :attr:`~deap.base.Fitness.weights` argument must be a tuple so that multi
objective and single objective fitnesses can be treated the same way. A
:class:`FitnessMulti` would be created the same way but using ``weights=(1.0,
-1.0)`` rendering a fitness that maximize the first objective and minimize the
second one. The weights can also be used to variate the importance of each
objective one against another. This means that the weights can be any real
number and only the sign is used to determine if a maximization of
minimization is done. An example of where the weights can be useful is in the
crowding distance sort made in the NSGA-II selection algorithm.

Individual
----------
Simply by thinking of the different flavours of evolutionary algorithms (GA,
GP, ES, PSO, DE, ...), we notice that an extremely large variety of
individuals are possible. Here is a guide on how to create some of those
individuals using the :mod:`~deap.creator` and initializing them using a
:class:`~deap.base.Toolbox`.

List of Floats
++++++++++++++
The first individual created will be a simple list containing floats. In order
to produce this kind of individual, we need to create an
:class:`Individual` class, using the creator, that will inherit from the
standard :class:`list` and have a :attr:`fitness` attribute. Then we will
initialize this list using the :func:`~deap.tools.initRepeat` helper function
that will repeat ``n`` times the float generator that has been registered
under the :func:`attr_float` alias of the toolbox. Note that the
:func:`attr_float` is a direct reference to the :func:`~random.random`
function.
::

	from deap import base
	from deap import creator
	from deap import tools
	
	import random
	
	creator.create("FitnessMax", base.Fitness, weights=(1.0,))
	creator.create("Individual", list, fitness=creator.FitnessMax)
	
	toolbox = base.Toolbox()
	toolbox.register("attr_float", random.random)
	toolbox.register("individual", tools.initRepeat, creator.Individual,
	    toolbox.attr_float, n=IND_SIZE)

Calling :func:`toolbox.individual` will readily return a complete individual
composed of ``IND_SIZE`` floating point numbers with a maximizing single
objective fitness attribute.

Permutation
+++++++++++
An individual for the permutation representation is almost similar to the
general list individual. In fact they both inherit from the basic
:class:`list` type. The only difference is that instead of filling the list
with a series of floats, we need to generate a random permutation and provide
that permutation to the individual. First, the individual class is created the
exact same way as the previous one. Then, an :func:`indices` function is added
to the toolbox referring to the :func:`~random.sample` function, sample is
used instead of :func:`~random.shuffle` because this last one does not return
the shuffled list. The indices function returns a complete permutation of the
numbers between ``0`` and ``IND_SIZE - 1``. Finally, the individual is
initialized with the :func:`~deap.tools.initIterate` function which gives to
the individual an iterable of what is produced by the call to the indices
function.
::

	from deap import base
	from deap import creator
	from deap import tools
	
	import random
	
	creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
	creator.create("Individual", list, fitness=creator.FitnessMin)
	
	toolbox = base.Toolbox()
	toolbox.register("indices", random.sample, range(IND_SIZE), IND_SIZE)
	toolbox.register("individual", tools.initIterate, creator.Individual,
	    toolbox.indices)

Calling :func:`toolbox.individual` will readily return a complete individual
that is a permutation of the integers ``0`` to ``IND_SIZE`` with a minimizing
single objective fitness attribute.

Arithmetic Expression
+++++++++++++++++++++
The next individual that is commonly used is a prefix tree of mathematical
expressions. This time a :class:`~deap.gp.PrimitiveSet` must be defined
containing all possible mathematical operators that our individual can use.
Here the set is called ``MAIN`` and has a single variable defined by the
arity. Operators :func:`~operator.add`, :func:`~operator.sub`, and
:func:`~operator.mul` are added to the primitive set with each an arity of 2.
Next, the :class:`Individual` class is created as before but having an
additional static attribute :attr:`pset` set to remember the global primitive
set. This time the content of the individuals will be generated by the
:func:`~deap.gp.genRamped` function that generate trees in a list format based
on a ramped procedure. Once again, the individual is initialised using the
:func:`~deap.tools.initIterate` function to give the complete generated
iterable to the individual class.
::

	from deap import base
	from deap import creator
	from deap import gp
	from deap import tools
	
	import operator
	
	pset = gp.PrimitiveSet("MAIN", arity=1)
	pset.addPrimitive(operator.add, 2)
	pset.addPrimitive(operator.sub, 2)
	pset.addPrimitive(operator.mul, 2)
	
	creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
	creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin,
	    pset=pset)
	
	toolbox = base.Toolbox()
	toolbox.register("expr", gp.genRamped, pset=pset, min_=1, max_=2)
	toolbox.register("individual", tools.initIterate, creator.Individual,
	    toolbox.expr)

Calling :func:`toolbox.individual` will readily return a complete individual
that is an arithmetic expression in the form of a prefix tree with a
minimizing single objective fitness attribute.

Evolution Strategy
++++++++++++++++++
Evolution strategies individuals are slightly different as they contain
generally two list, one for the actual individual and one for its mutation
parameters. This time instead of using the list base class we will inherit
from an :class:`array.array` for both the individual and the strategy. Since
there is no helper function to generate two different vectors in a single
object we must define this function our-self. The :func:`initES` function
receives two classes and instantiate them generating itself the random numbers
in the intervals provided for individuals of a given size.
::

	from deap import base
	from deap import creator
	from deap import tools
	
	import array
	import random
	
	creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
	creator.create("Individual", array.array, typecode="d",
	    fitness=creator.FitnessMin, strategy=None)
	creator.create("Strategy", array.array, typecode="d")

	def initES(icls, scls, size, imin, imax, smin, smax):
	    ind = icls(random.uniform(imin, imax) for _ in range(size))
	    ind.strategy = scls(random.uniform(smin, smax) for _ in range(size))
	    return ind

	toolbox = base.Toolbox()
	toolbox.register("individual", initES, creator.Individual,
	    creator.Strategy, IND_SIZE, MIN_VALUE, MAX_VALUE, MIN_STRATEGY,
	    MAX_STRATEGY)

Calling :func:`toolbox.individual` will readily return a complete evolution
strategy with a strategy vector and a minimizing single objective fitness
attribute.

Particle
++++++++
A particle is another special type of individual as it usually has a speed and
generally remember its best position. This type of individual is created (once
again) the same way inheriting from a list. This time :attr:`speed`,
:attr:`best` and speed limits attributes are added to the object. Again, an
initialization function :func:`initParticle` is also registered to produce the
individual receiving the particle class, size, domain, and speed limits as
arguments.
::

	from deap import base
	from deap import creator
	from deap import tools
	
	import random
	
	creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))
	creator.create("Particle", list, fitness=creator.FitnessMax, speed=None, 
	    smin=None, smax=None, best=None)
	
	def initParticle(pcls, size, pmin, pmax, smin, smax):
	    part = pcls(random.uniform(pmin, pmax) for _ in xrange(size)) 
	    part.speed = [random.uniform(smin, smax) for _ in xrange(size)]
	    part.smin = smin
	    part.smax = smax
	    return part
	
	toolbox = base.Toolbox()
	toolbox.register("particle", initParticle, creator.Particle, size=2,
	    pmin=-6, pmax=6, smin=-3, smax=3)

Calling :func:`toolbox.individual` will readily return a complete particle
with a speed vector and a maximizing two objectives fitness attribute.

A Funky One
+++++++++++
Supposing your problem have very specific needs. It is also possible to build
custom individuals very easily. The next individual created is a list of
alternating integers and floating point numbers, using the
:func:`~deap.tools.initCycle` function.
::

	from deap import base
	from deap import creator
	from deap import tools
	
	import random
	
	creator.create("FitnessMax", base.Fitness, weights=(1.0, 1.0))
	creator.create("Individual", list, fitness=creator.FitnessMax)
	
	toolbox = base.Toolbox()
	
	toolbox.register("attr_int", random.randint, INT_MIN, INT_MAX)
	toolbox.register("attr_flt", random.uniform, FLT_MIN, FLT_MAX)
	toolbox.register("individual", tools.initCycle, creator.Individual, 
	    (toolbox.attr_int, toolbox.attr_flt), n=N_CYCLES)

Calling :func:`toolbox.individual` will readily return a complete individual
of the form ``[int float int float ... int float]`` with a maximizing two
objectives fitness attribute.
	
Population
----------
Population are much like individuals, instead of being initialized with
attributes it is filled with individuals, strategies or particles.

Bag
+++
A bag population is the most commonly used type, it has no particular ordering
although it is generally implemented using a list. Since the bag has no
particular attribute it does not need any special class. The population is
initialized using directly the toolbox and the :func:`~deap.tools.initRepeat`
function.
::

	toolbox.register("population", tools.initRepeat, list, toolbox.individual)

Calling :func:`toolbox.population` will readily return a complete population
in a list providing a number of times the repeat helper must be repeated as an
argument of the population function.

Grid
++++
A grid population is a special case of structured population where
neighbouring individuals have a direct effect on each other. The individuals
are distributed in grid where each cell contains a single individual. (Sadly?)
It is no different than the list implementation of the bag population other
that it is composed of lists of individuals.
::

	toolbox.register("row", tools.initRepeat, list, toolbox.individual,
	    n=N_COL)
	toolbox.register("population", tools.initRepeat, list, toolbox.row,
	    n=N_ROW)

Calling :func:`toolbox.population` will readily return a complete population
where the individuals are accessible using two indices for example
``pop[r][c]``. For the moment there is no algorithm specialized for structured
population, we are waiting your submissions.

Swarm
+++++
A swarm is used in particle swarm optimization, it is different in the sens
that it contains a network of communication. The simplest network is the
complete connection where each particle knows the best position of that ever
been visited by any other particle. This is generally implemented by copying
that global best position to a :attr:`gbest` attribute and the global best
fitness to a :attr:`gbestfit` attribute.
::

	creator.create("Swarm", list, gbest=None, gbestfit=creator.FitnessMax)
	
	toolbox.register("swarm", tools.initRepeat, creator.Swarm,
	    toolbox.particle)

Calling :func:`toolbox.population` will readily return a complete swarm. After
each evaluation the :attr:`gbest` and :attr:`gbestfit` are set to reflect the
best found position and fitness.

Demes
+++++
A deme is a sub-population that is contained in a population. It is similar
has an island in the island model. Demes being only sub-population are in fact
no different than population other than by their names. Here we create a
population containing 3 demes each having a different number of individuals
using the *n* argument of the :func:`~deap.tools.initRepeat` function.
::

	toolbox.register("deme", tools.initRepeat, list, toolbox.individual)
	
	DEME_SIZES = 10, 50, 100
	
	population = [toolbox.deme(n=i) for i in DEME_SIZES]

Seeding a Population
++++++++++++++++++++
Sometimes, a first guess population can be used to initialize an evolutionary
algorithm. The key idea to initialize a population with not random individuals
is to have an individual initializer that takes a content as argument.
::

	from deap import base
	from deap import creator

	import json

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

The population will be initialized from the file ``my_guess.json`` that shall
contain a list of first guess individuals. This initialization can be combined
with a regular initialization to have part random and part not random
individuals. Note that the definition of :func:`initIndividual` and the
registration of :func:`individual_guess` are optional as the default
constructor of a list is similar. Removing those lines leads to the following.
::

	toolbox.register("population_guess", initPopulation, list, creator.Individual, "my_guess.json")

