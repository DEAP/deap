.. _creating-types:

Creating Types
==============
This tutorial shows how types are created using the creator and initialized
using the toolbox.

Fitness
-------
The provided :class:`~deap.base.Fitness` class is an abstract class that needs a
:attr:`~deap.base.Fitness.weights` attribute in order to be functional. A
minimizing fitness is built using negatives weights, while a maximizing fitness
has positive weights. For example, the following line creates, in the
:mod:`~deap.creator`, a ready to use single objective minimizing fitness named
:class:`FitnessMin`. 

.. literalinclude:: /code/tutorials/part_2/2_1_fitness.py
   :lines: 6

The :func:`~deap.creator.create` function takes at least two arguments, a name for the newly created class and a base class. Any subsequent argument becomes an attribute of the class.
As specified in the :class:`~deap.base.Fitness` documentation, the :attr:`~deap.base.Fitness.weights` attribute must be a tuple so that multi-objective and single objective fitnesses can be treated the same way. A
:class:`FitnessMulti` would be created the same way but using:

.. literalinclude:: /code/tutorials/part_2/2_1_fitness.py
   :lines: 9

This code produces a fitness that minimize the first objective and maximize the
second one. The weights can also be used to vary the importance of each
objective one against another. This means that the weights can be any real
number and only the sign is used to determine if a maximization or minimization
is done. An example of where the weights can be useful is in the crowding
distance sort made in the NSGA-II selection algorithm.

Individual
----------
Simply by thinking about the different flavors of evolutionary algorithms (GA,
GP, ES, PSO, DE, ...), we notice that an extremely large variety of individuals
are possible, reinforcing the assumption that all types cannot be made available
by developers. Here is a guide on how to create some of those individuals using
the :mod:`~deap.creator` and initializing them using a
:class:`~deap.base.Toolbox`.

.. warning::
   
   Before inheriting from :class:`numpy.ndarray` you should **absolutely** read
   the :doc:`/tutorials/advanced/numpy` tutorial and have a look at the
   :doc:`/examples/ga_onemax_numpy` example!

.. _list-of-floats:

List of Floats
++++++++++++++
The first individual created will be a simple list containing floats. In order
to produce this kind of individual, we need to create an :class:`Individual`
class, using the creator, that will inherit from the standard :class:`list` type
and have a :attr:`fitness` attribute.

.. Then, we will initialize this list using
.. the :func:`~deap.tools.initRepeat` helper function that will repeat ``n`` times
.. the float generator that has been registered under the :func:`attr_float` alias
.. of the toolbox. Note that the :func:`attr_float` is a direct reference to the
.. :func:`~random.random` function.

.. literalinclude:: /code/tutorials/part_2/2_2_1_list_of_floats.py
   :lines: 2,5-18

The newly introduced :meth:`~deap.base.Toolbox.register` method takes at least two arguments; an alias and a function assigned to this alias. Any subsequent argument is passed to the function when called (à la :func:`functools.partial`).
Thus, the preceding code creates two aliases in the toolbox; ``attr_float`` and ``individual``. The first one redirects to the :func:`random.random` function. The second one is a shortcut to the :func:`~deap.tools.initRepeat` function, fixing its :data:`container` argument to the :class:`creator.Individual` class, its :data:`func` argument to the :func:`toolbox.attr_float` function, and its number of repetitions argument to ``IND_SIZE``.

Now, calling :func:`toolbox.individual` will call :func:`~deap.tools.initRepeat` with the fixed arguments and return a complete :class:`creator.Individual`
composed of ``IND_SIZE`` floating point numbers with a maximizing single
objective :attr:`fitness` attribute.

Variations of this type are possible by inheriting from :class:`array.array`
or :class:`numpy.ndarray` as following.

.. literalinclude:: /code/tutorials/part_2/2_2_1_list_of_floats.py
   :lines: 20,21

Type inheriting from arrays needs a *typecode* on initialization, just as the
original class.

.. _permutation:

Permutation
+++++++++++
An individual for the permutation representation is almost similar to the
general list individual. In fact they both inherit from the basic :class:`list`
type. The only difference is that instead of filling the list with a series of
floats, we need to generate a random permutation and provide that permutation to
the individual.

.. First, the individual class is created the exact same way as the
.. previous one. Then, an :func:`indices` function is added to the toolbox
.. referring to the :func:`~random.sample` function. Sample is used instead of
.. :func:`~random.shuffle` because the latter does not return the shuffled list.
.. The indices function returns a complete permutation of the numbers between ``0``
.. and ``IND_SIZE - 1``. Finally, the individual is initialized with the
.. :func:`~deap.tools.initIterate` function which gives to the individual an
.. iterable of what is produced by the call to the indices function.

.. literalinclude:: /code/tutorials/part_2/2_2_2_permutation.py
   :lines: 2-

The first registered function ``indices`` redirects to the :func:`random.sample` function with its arguments fixed to sample ``IND_SIZE`` numbers from the given range. The second registered function ``individual`` is a shortcut to the :func:`~deap.tools.initIterate` function, with its :data:`container` argument set to the :class:`creator.Individual` class and its :data:`generator` argument to the :func:`toolbox.indices` alias.

Calling :func:`toolbox.individual` will call :func:`~deap.tools.initIterate` with the fixed arguments and return a complete :class:`creator.Individual`
composed of permutation with a maximizing single
objective :attr:`fitness` attribute.

.. _arithmetic-expr:

Arithmetic Expression
+++++++++++++++++++++
The next individual that is commonly used is a prefix tree of mathematical
expressions. This time, a :class:`~deap.gp.PrimitiveSet` must be defined
containing all possible mathematical operators that our individual can use.
Here, the set is called ``MAIN`` and has a single variable defined by the
arity_.  Operators :func:`~operator.add`, :func:`~operator.sub`, and
:func:`~operator.mul` are added to the primitive set with each an arity of 2.
Next, the :class:`Individual` class is created as before with the addition of a
static attribute :attr:`pset` to remember the global primitive set. This time,
the content of the individuals will be generated by the
:func:`~deap.gp.genHalfAndHalf` function that generates trees in a list format based
on a ramped procedure. Once again, the individual is initialized using the
:func:`~deap.tools.initIterate` function to give the complete generated iterable
to the individual class.

.. literalinclude:: /code/tutorials/part_2/2_2_3_arithmetic_expression.py
   :lines: 2-

.. _arity: http://en.wikipedia.org/wiki/Arity

Calling :func:`toolbox.individual` will readily return a complete individual
that is an arithmetic expression in the form of a prefix tree with a
minimizing single objective fitness attribute.

Evolution Strategy
++++++++++++++++++
Evolution strategies individuals are slightly different as they contain
generally two lists, one for the actual individual and one for its mutation
parameters. This time, instead of using the list base class, we will inherit from
an :class:`array.array` for both the individual and the strategy. Since there is
no helper function to generate two different vectors in a single object, we must
define this function ourselves. The :func:`initES` function receives two classes
and instantiates them generating itself the random numbers in the ranges
provided for individuals of a given size.

.. literalinclude:: /code/tutorials/part_2/2_2_4_evolution_strategy.py
   :lines: 2-

Calling :func:`toolbox.individual` will readily return a complete evolution
strategy with a strategy vector and a minimizing single objective fitness
attribute.

Particle
++++++++
A particle is another special type of individual as it usually has a speed and
generally remember its best position. This type of individual is created (once
again) the same way as inheriting from a list. This time, :attr:`speed`,
:attr:`best` and speed limits attributes are added to the object. Again, an
initialization function :func:`initParticle` is also registered to produce the
individual receiving the particle class, size, domain, and speed limits as
arguments.

.. literalinclude:: /code/tutorials/part_2/2_2_5_particle.py
   :lines: 2-

Calling :func:`toolbox.individual` will readily return a complete particle with
a speed vector and a maximizing two objectives fitness attribute.

.. _funky:

A Funky One
+++++++++++
Supposing your problem have very specific needs. It is also possible to build
custom individuals very easily. The next individual created is a list of
alternating integers and floating point numbers, using the
:func:`~deap.tools.initCycle` function.

.. literalinclude:: /code/tutorials/part_2/2_2_6_funky_one.py
   :lines: 2-

Calling :func:`toolbox.individual` will readily return a complete individual of
the form ``[int float int float ... int float]`` with a maximizing two
objectives fitness attribute.

.. _population:

Population
----------
Population are much like individuals. Instead of being initialized with
attributes, it is filled with individuals, strategies or particles.

Bag
+++
A bag population is the most commonly used type. It has no particular ordering
although it is generally implemented using a list. Since the bag has no
particular attribute, it does not need any special class. The population is
initialized using the toolbox and the :func:`~deap.tools.initRepeat`
function directly.

.. literalinclude:: /code/tutorials/part_2/2_3_1_bag.py
   :lines: 17

Calling :func:`toolbox.population` will readily return a complete population in
a list, providing a number of times the repeat helper must be repeated as an
argument of the population function. The following example produces a population
with 100 individuals.

.. literalinclude:: /code/tutorials/part_2/2_3_1_bag.py
   :lines: 19

Grid
++++
A grid population is a special case of structured population where neighbouring
individuals have a direct effect on each other. The individuals are distributed
in grid where each cell contains a single individual. However, its
implementation is no different than the list of the bag
population, other that it is composed of lists of individuals.

.. literalinclude:: /code/tutorials/part_2/2_3_2_grid.py
   :lines: 20-21

Calling :func:`toolbox.population` will readily return a complete population
where the individuals are accessible using two indices, for example
``pop[r][c]``. For the moment, there is no algorithm specialized for structured
population, we are awaiting your submissions.

Swarm
+++++
A swarm is used in particle swarm optimization. It is different in the sense
that it contains a communication network. The simplest network is the complete
connection, where each particle knows the best position that have ever been
visited by any particle. This is generally implemented by copying that global
best position to a :attr:`gbest` attribute and the global best fitness to a
:attr:`gbestfit` attribute.

.. literalinclude:: /code/tutorials/part_2/2_3_3_swarm.py
   :lines: 11,23

Calling :func:`toolbox.population` will readily return a complete swarm. After
each evaluation the :attr:`gbest` and :attr:`gbestfit` should be set by the
algorithm to reflect the best found position and fitness.

Demes
+++++
A deme is a sub-population that is contained in a population. It is similar has
an island in the island model. Demes, being only sub-populations, are in fact no
different than populations, aside from their names. Here, we create a population
containing 3 demes, each having a different number of individuals using the *n*
argument of the :func:`~deap.tools.initRepeat` function.

.. literalinclude:: /code/tutorials/part_2/2_3_4_demes.py
   :lines: 17-20

Seeding a Population
++++++++++++++++++++
Sometimes, a first guess population can be used to initialize an evolutionary
algorithm. The key idea to initialize a population with not random individuals
is to have an individual initializer that takes a content as argument.

.. literalinclude:: /code/tutorials/part_2/2_3_5_seeding_a_population.py
   :lines: 2-

The population will be initialized from the file ``my_guess.json`` that shall
contain a list of first guess individuals. This initialization can be combined
with a regular initialization to have part random and part not random
individuals. Note that the definition of :func:`initIndividual` and the
registration of :func:`individual_guess` are optional as the default constructor
of a list is similar. Removing those lines leads to the following: ::

    toolbox.register("population_guess", initPopulation, list, creator.Individual, "my_guess.json")

