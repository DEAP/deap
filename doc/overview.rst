Overview
========
If your are used to an other evolutionary algorithm framework, you'll notice
we do things differently with DEAP. Instead of limiting you with predefined
types, we provide ways of creating the appropriate ones. Instead of providing
closed initializers, we enable you to customize them as you wish. Instead of
suggesting unfit operators, we explicitly ask you to choose them wisely.
Instead of implementing many sealed algorithms, we allow you to write the one
that fit all your needs. This tutorial will present a quick overview of what
DEAP is all about along with what every DEAP program is made of.

Types
-----
The first thing to do is to think of the appropriate type for your problem.
Then, instead of looking in the list of available types, DEAP enables you to
build your own. This is done with
the :mod:`~deap.creator` module. Creating an appropriate type might seems
overwhelming but the creator makes it very easy. In fact, this is usually done
in a single line. For example, the following creates a :class:`FitnessMin` class
for a minimization problem and an :class:`Individual` class that is derived
from a list with a fitness attribute set to the just created fitness.

.. literalinclude:: /code/tutorials/part_1/1_where_to_start.py
   :lines: 2-4

That's it. More on creating types can be found in the :doc:`tutorials/basic/part1`
tutorial.

Initialization
--------------
Once the types are created you need to fill them with sometimes random values,
sometime guessed ones. Again, DEAP provides an easy mechanism to do just that.
The :class:`~deap.base.Toolbox` is a container for tools of all sorts
including initializers that can do what is needed of them. The following takes
on the last lines of code to create the initializers for individuals
containing random floating point numbers and for a population that contains
them.

.. literalinclude:: /code/tutorials/part_1/1_where_to_start.py
   :lines: 7-16

This creates functions to initialize populations from individuals that are
themselves initialized with random float numbers. The functions are registered
in the toolbox with there default arguments under the given name. For example,
it will be possible to call the function :func:`toolbox.population` to
instantly create a population.
More initialization methods
are found in the :doc:`tutorials/basic/part1` tutorial and the various 
:doc:`examples/index`.

Operators
---------
Operators are just like initalizers, excepted that some are already
implemented in the :mod:`~deap.tools` module. Once you've chose the perfect
ones simply register them in the toolbox. In addition you must create your
evaluation function. This is how it is done in DEAP.

.. literalinclude:: /code/tutorials/part_1/1_where_to_start.py
   :lines: 19-25

The registered functions are renamed by the toolbox to allows genericity so
that the algorithm does not depend on operators name. Note also that fitness
values must be iterable, that is why we return tuple in the evaluate function.
More on this in the :doc:`tutorials/basic/part2` tutorial and :doc:`examples/index`.

Algorithms
----------
Now that everything is ready, we can start to write our own algorithm. It is
usually done in a main function. For the purpose of completeness we will
develop the complete generational algorithm.

.. literalinclude:: /code/tutorials/part_1/1_where_to_start.py
   :lines: 28-64

It is also possible to use one of the four algorithms readily
available in the :mod:`~deap.algorithms` module, or build from some building
blocks called variations also available in this module.
