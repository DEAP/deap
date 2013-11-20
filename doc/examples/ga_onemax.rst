.. _ga-onemax:

===============
One Max Problem
===============

This is the first complete example built with DEAP. It will help new users to
overview some of the framework possibilities. The problem is very simple, we
search for a :data:`1` filled list individual. This problem is widely used in
the evolutionary computation community since it is very simple and it
illustrates well the potential of evolutionary algorithms.

Setting Things Up
=================

Here we use the one max problem to show how simple can be an evolutionary
algorithm with DEAP. The first thing to do is to elaborate the structures of
the algorithm. It is pretty obvious in this case that an individual that can
contain a series of `booleans` is the most interesting kind of structure
available. DEAP does not contain any explicit individual structure since it is
simply a container of attributes associated with a fitness. Instead, it
provides a convenient method for creating types called the creator.

First of all, we need to import some modules.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 16-20

-------
Creator
-------

The creator is a class factory that can build at run-time new classes that
inherit from a base classe. It is very useful since an individual can be any
type of container from list to n-ary tree. The creator allows build complex
new structures convenient for evolutionary computation.

Let see an example of how to use the creator to setup an individual that
contains an array of booleans and a maximizing fitness. We will first need to
import the :mod:`deap.base` and :mod:`deap.creator` modules.

The creator defines at first a single function :func:`~deap.creator.create`
that is used to create types. The :func:`~deap.creator.create` function takes
at least 2 arguments plus additional optional arguments. The first argument
*name* is the actual name of the type that we want to create. The second
argument *base* is the base classe that the new type created should inherit
from. Finally the optional arguments are members to add to the new type, for
example a :attr:`fitness` for an individual or :attr:`speed` for a particle.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 22-23

The first line creates a maximizing fitness by replacing, in the base type
:class:`~deap.base.Fitness`, the pure virtual
:attr:`~deap.base.Fitness.weights` attribute by ``(1.0,)`` that means to
maximize a single objective fitness. The second line creates an
:class:`Individual` class that inherits the properties of :class:`list` and
has a :attr:`fitness` attribute of the type :class:`FitnessMax` that was just
created.

In this last step, two things are of major importance. The first is the comma
following the ``1.0`` in the weights declaration, even when implementing a
single objective fitness, the weights (and values) must be iterable. We
won't repeat it enough, in DEAP single objective is a special case of
multiobjective. The second important thing is how the just created
:class:`FitnessMax` can be used directly as if it was part of the
:mod:`~deap.creator`. This is not magic.

-------
Toolbox
-------
A :class:`~deap.base.Toolbox` can be found in the base module. It is intended
to store functions with their arguments. The toolbox contains two
methods, :meth:`~deap.base.Toolbox.register` and
:meth:`~deap.base.Toolbox.unregister` that are used to do the tricks.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 25-31

In this code block we registered a generation function and two initialization
functions. The generator :meth:`toolbox.attr_bool` when called, will draw a
random integer between 0 and 1. The two initializers for their part will
produce respectively initialized individuals and populations.

Again, looking a little closer shows that their is no magic. The registration
of tools in the toolbox only associates an *alias* to an already existing
function and freezes part of its arguments. This allows to call the alias as
if the majority of the (or every) arguments have already been given. For
example, the :meth:`attr_bool` generator is made from the
:func:`~random.randint` that takes two arguments *a* and *b*, with ``a <= n <=
b``, where *n* is the returned integer. Here, we fix ``a = 0`` and ``b = 1``.

It is the same thing for the initializers. This time, the
:func:`~deap.tools.initRepeat` is frozen with predefined arguments. In the
case of the :meth:`individual` method, :func:`~deap.tools.initRepeat` takes 3
arguments, a class that is a container -- here the :class:`Individual` is
derived from a :class:`list` --, a function to fill the container and the
number of times the function shall be repeated. When called, the
:meth:`individual` method will thus return an individual initialized with what
would be returned by 100 calls to the :meth:`attr_bool` method. Finally, the
:meth:`population` method uses the same paradigm, but we don't fix the number
of individuals that it should contain.

The Evaluation Function
=======================

The evaluation function is pretty simple in this case, we need to count the
number of ones in the individual. This is done by the following lines of code. 

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 33-34

The returned value must be an iterable of length equal to the number of
objectives (weights).
   
The Genetic Operators
=====================

There is two way of using operators, the first one, is to simply call the
function from the :mod:`~deap.tools` module and the second one is to register
them with their argument in a toolbox as for the initialization methods. The
most convenient way is to register them in the toolbox, because it allows to
easily switch between operators if desired. The toolbox method is also used in
the algorithms, see the :ref:`short-ga-onemax` for an example.

Registering the operators and their default arguments in the toolbox is done
as follow. 

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 37-40

The evaluation is given the alias evaluate. Having a single argument being the
individual to evaluate we don't need to fix any, the individual will be given
later in the algorithm. The mutation, for its part, needs an argument to be
fixed (the independent probability of each attribute to be mutated *indpb*).
In the algorithms the :meth:`mutate` function is called with the signature
``mutant, = toolbox.mutate(mutant)``. This is the most convenient way because
each mutation takes a different number of arguments, having those arguments
fixed in the toolbox leave open most of the possibilities to change the
mutation (or crossover, or selection, or evaluation) operator later in your
researches.

Evolving the Population
=======================

Once the representation and the operators are chosen, we have to define an
algorithm. A good habit to take is to define the algorithm inside a function,
generally named ``main()``.

-----------------------
Creating the Population
-----------------------

Before evolving it, we need to instantiate a population. This step is done
effortless using the method we registered in the toolbox. 

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 42, 45


``pop`` will be a :class:`list` composed of 300 individuals, *n* is the
parameter left open earlier in the toolbox. The next thing to do is to
evaluate this brand new population.
	
.. literalinclude:: /../examples/ga/onemax.py
   :lines: 50-53

We first :func:`map` the evaluation function to every individual, then assign
their respective fitness. Note that the order in ``fitnesses`` and
``population`` are the same.

-----------------------
The Appeal of Evolution
-----------------------

The evolution of the population is the last thing to accomplish. Let say that
we want to evolve for a fixed number of generation :data:`NGEN`, the
evolution will then begin with a simple for statement.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 57-59

Is that simple enough? Lets continue with more complicated things, selecting,
mating and mutating the population. The crossover and mutation operators
provided within DEAP usually take respectively 2 and 1 individual(s) on input
and return 2 and 1 modified individual(s), they also modify inplace these
individuals.

In a simple GA, the first step is to select the next generation.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 61-64

This step creates an offspring list that is an exact copy of the selected
individuals. The :meth:`toolbox.clone` method ensure that we don't own a
reference to the individuals but an completely independent instance.

Next, a simple GA would replace the parents by the produced children
directly in the population. This is what is done by the following lines
of code, where a crossover is applied with probability :data:`CXPB` and a
mutation with probability :data:`MUTPB`. The ``del`` statement simply
invalidate the fitness of the modified individuals.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 66-76

The population now needs to be re-evaluated, we then apply the evaluation as
seen earlier, but this time only on the individuals with an invalid fitness. 

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 78-82

And finally, last but not least, we replace the old population by the
offspring. 

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 87

This is the end of the evolution part, it will continue until the predefined
number of generation are accomplished.

Although, some statistics may be gathered on the population, the following
lines print the min, max, mean and standard deviation of the population.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 89-100

A :class:`~deap.tools.Statistics` object has been defined to facilitate how
statistics are gathered. It is not presented here so that we can focus on the
core and not the gravitating helper objects of DEAP.

The complete :example:`ga/onemax`.
