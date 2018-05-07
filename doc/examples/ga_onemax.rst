.. _ga-onemax:

===============
One Max Problem
===============

This is the first complete example built with DEAP. It will help new users to
overview some of the framework's possibilities and illustrate the potential
of evolutionary algorithms in general. The problem itself is both very simple
and widely used in the evolutionary computational community. We will create a
population of individuals consisting of integer vectors randomly filled with ``0``
and ``1``. Then we let our population evolve until one of its members contains
only ``1`` and no ``0`` anymore.

Setting Things Up
=================

In order to solve the One Max problem, we need a bunch of ingredients. First
we have to define our individuals, which will be lists of integer values,
and to generate a population using them. Then we will add some functions and
operators taking care of the evaluation and evolution of our population and
finally put everything together in script.

But first of all, we need to import some modules.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 20-24

-------
Creator
-------

Since the actual structure of the required individuals in genetic algorithms
does strongly depend on the task at hand, DEAP does not contain any explicit
structure. It will rather provide a convenient method for creating containers
of attributes, associated with fitnesses, called the :mod:`deap.creator`.
Using this method we can create custom individuals in a very simple way.
     
The ``creator`` is a class factory that can build new classes at run-time.
It will be called with first the desired *name* of the new class, second
the *base class* it will inherit, and in addition any subsequent arguments
you want to become attributes of your class. This allows us to build new and
complex structures of any type of container from lists to n-ary trees.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 26-27

First we will define the class :class:`FitnessMax`. It will inherit the
:class:`Fitness` class of the :mod:`deap.base` module and contain an additional
attribute called *weights*. Please mind the value of *weights* to be the tuple
``(1.0,)``. This way we will be maximizing a single objective fitness.
We can't repeat it enough, in DEAP single objectives is a special case of
multi objectives.

Next we will create the class :class:`Individual`, which will inherit the
class :class:`list` and contain our previously defined :class:`FitnessMax`
class in its *fitness* attribute. Note that upon creation all our defined
classes will be part of the ``creator`` container and can be called directly.

-------
Toolbox
-------
Now we will use our custom classes to create types representing our individuals
as well as our whole population.

All the objects we will use on our way, an individual, the population, as
well as all functions, operators, and arguments will be stored in a DEAP container
called :class:`~deap.base.Toolbox`. It contains two methods for adding and removing
content, :meth:`~deap.base.Toolbox.register` and :meth:`~deap.base.Toolbox.unregister`.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 29,31,36,38,41-42,45

In this code block we register a generation function :meth:`toolbox.attr_bool()`
and two initialization ones :meth:`individual` and :meth:`population`.
:meth:`toolbox.attr_bool`, when called, will draw a
random integer between 0 and 1. The two initializers, on the other hand, will
instantiate an individual or population.

The registration of the tools to the toolbox only associates *aliases*
to the already existing functions and freezes part of their arguments.
This allows us to fix an arbitrary amount of argument at certain values
so we only have to specify the remaining ones when calling the method.
For example, the :meth:`attr_bool` generator is made from the
:func:`~random.randint` function that takes two arguments *a* and *b*, with ``a <= n <=
b``, where *n* is the returned integer. Here, we fix ``a = 0`` and ``b = 1``.

Our individuals will be generated using the function :func:`~deap.tools.initRepeat`.
Its first argument is a container class, in our example the :class:`Individual` one we
defined in the previous section. This container will be filled using the method
:meth:`attr_bool`, provided as second argument, and will contain 100 integers, as
specified using the third argument. When called, the
:meth:`individual` method will thus return an individual initialized with what
would be returned by calling the :meth:`attr_bool` method 100 times. Finally, the
:meth:`population` method uses the same paradigm, but we don't fix the number
of individuals that it should contain.

The Evaluation Function
=======================

The evaluation function is pretty simple in our example. We just need to count the
number of ones in an individual.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 48-49

The returned value must be an iterable of a length equal to the number of
objectives (weights).
   
The Genetic Operators
=====================

Within DEAP there are two ways of using operators. We can either simply call a
function from the :mod:`~deap.tools` module or register it with its arguments
in a toolbox, as we have already seen for our initialization methods. The most
convenient way, however, is to register them in the toolbox, because this allows us to
easily switch between the operators if desired. The toolbox method is also used
when working with the :mod:`algorithms` module. See the :ref:`short-ga-onemax`
for an example.

Registering the genetic operators required for the evolution in our One Max problem
and their default arguments in the toolbox is done as follows. 

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 55,58,62,68

The evaluation will be performed by calling the alias *evaluate*. It is important
to not fix its argument in here. We will need it later on to apply the function to each
separate individual in our population. The mutation, on the other hand, needs an argument to be
fixed (the independent probability of each attribute to be mutated *indpb*).

Evolving the Population
=======================

Once the representation and the genetic operators are chosen, we will define an
algorithm combining all the individual parts and performing the evolution of our
population until the One Max problem is solved. It is good style in programming to do so
within a function, generally named ``main()``.

-----------------------
Creating the Population
-----------------------

First of all, we need to actually instantiate our population. But this step is
effortlessly done using the :meth:`population` method we registered in our toolbox
earlier on.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 72,77


``pop`` will be a :class:`list` composed of 300 individuals. Since we left the
parameter *n* open during the registration of the :meth:`population` method in our
toolbox, we are free to create populations of arbitrary size.

The next thing to do is to evaluate our brand new population.
	
.. literalinclude:: /../examples/ga/onemax.py
   :lines: 87-90

We :func:`map` the evaluation function to every individual and then assign
their respective fitness. Note that the order in ``fitnesses`` and
``population`` is the same.

-----------------------
Performing the Evolution
-----------------------

The evolution of the population is the final step we have to accomplish.
Recall, our individuals consist of 100 integer numbers and we want to evolve
our population until we got at least one individual consisting of only
``1`` and no ``0``. So all we have to do is to obtain the fitness values
of the individuals

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 94-95

and evolve our population until one of them reaches ``100`` or the number of
generations reaches ``1000``.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 97-99,100-104

The evolution itself will be performed by selecting, mating, and mutating
the individuals in our population. 

In our simple example of a genetic algorithm, the first step is to select the
next generation.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 106-109

This will creates an *offspring* list, which is an exact copy of the selected
individuals. The :meth:`toolbox.clone` method ensure that we don't use a
reference to the individuals but an completely independent instance. This is
of utter importance since the genetic operators in toolbox will modify
the provided objects in-place.

Next, we will perform both the crossover (mating) and the mutation of the
produced children with a certain  probability of :data:`CXPB` and :data:`MUTPB`.
The ``del`` statement will invalidate the fitness of the modified offspring.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 111-112,115-116,120-123,126-128

The crossover (or mating) and mutation operators, provided within DEAP,
usually take respectively 2 or 1 individual(s) as input
and return 2 or 1 modified individual(s). In addition they modify those
individuals within the toolbox container and we do not need to reassign their results.
	   
Since the content of some of our offspring changed during the last step, we now need
to re-evaluate their fitnesses. To save time and resources, we just map those
offspring which fitnesses were marked invalid.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 130-134

And last but not least, we replace the old population by the
offspring. 

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 139

To check the performance of the evolution, we will calculate and
print the minimal, maximal, and mean values of the fitnesses of all individuals
in our population as well as their standard deviations.

.. literalinclude:: /../examples/ga/onemax.py
   :lines: 141-152

This evolution will now run until at least one of the individuals will be filled
with ``1`` exclusively.

A :class:`~deap.tools.Statistics` object is available within DEAP to facilitate the
gathering of the evolution's statistics. See the :ref:`short-ga-onemax` for an example.

The complete source code of this example: :example:`ga/onemax`.
