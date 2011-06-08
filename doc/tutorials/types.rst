Creating Types
==============
This tutorial shows how types are created using the creator and initialized using the toolbox.

Fitness
-------
The provided :class:`~deap.base.Fitness` class is an abstract class that needs
a :attr:`~deap.base.Fitness.weights` attribute in order to be functional. A
minimizing fitness is built using negatives weights. For example, the
following line creates, in the :mod:`~deap.creator`, a ready to use single
objective minimizing fitness named :class:`FitnessMin`. ::

   creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
   
The :attr:`~deap.base.Fitness.weights` argument must be a tuple so that multi
objective and single objective fitnesses can be treated the same way. A
:class:`FitnessMulti` would be created the same way but using ``(1.0, -1.0)``
rendering a fitness that maximize the first objective and minimize the second
one. The weights can also be used to variate the importance of each objective
one against another. This means that the weights can be any real number and
only the sign is used to determine if a maximization of minimization is done.
An example of where the weights can be useful is in the crowding distance sort
made in the NSGA-II selection algorithm.

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
	
	creator.create("FitnessMin", base.Fitness, weights=(1.0,))
	creator.create("Individual", list, fitness=creator.FitnessMin)
	
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
The next individual that is commonly used is a prefix tree of mathematical expressions. This time a :class:`~deap.gp.PrimitiveSet` must be defined containing all possible mathematical operators that our individual can use. Here the set is called ``MAIN`` and has a single variable defined by the arity. Operators :func:`~operator.add`, :func:`~operator.sub`, and :func:`~operator.mul` are added to the primitive set with each an arity of 2. Next, the :class:`Individual` class is created as before but having an additional static attribute :attr:`pset` set to remember the global primitive set. This time the content of the individuals will be generated by the :func:`~deap.gp.genRamped` function that generate trees in a list format based on a ramped procedure. Once again, the individual is initialised using the :func:`~deap.tools.initIterate` function to give the complete generated iterable to the individual class.
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
Evolution strategies individuals are slightly different as they contain generally two list, one for the actual individual and one for its mutation parameters. This time instead of using the list base class we will inherit from an :class:`array.array` for both the individual and the strategy. Since there is no helper function to generate two different vectors in a single object we must define this function our-self. The :func:`initES` function receives two classes and instantiate them generating itself the random numbers in the intervals provided for individuals of a given size.
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
A particle is another special type of individual as it usually has a speed and generally remember its best position. This type of individual is created (once again) the same way.
::

	creator.create("FitnessMax", base.Fitness, weights=(1.0,))
	creator.create("Particle", list, fitness=creator.FitnessMax, speed=list, 
	    smin=None, smax=None, best=None)

Population
----------
