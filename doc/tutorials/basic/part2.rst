.. _next-step:

Operators and Algorithms
========================

Before starting with complex algorithms, we will see some basis of DEAP.
First, we will start by creating simple individuals (as seen in the
:ref:`creating-types` tutorial) and make them interact with each other using
different operators. Afterwards, we will learn how to use the algorithms and
other tools.

A First Individual
------------------

First import the required modules and register the different functions required to create individuals that are a list of floats with a minimizing  two objectives fitness.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 2-16

The first individual can now be built by adding the appropriate line to the script.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 18

Printing the individual ``ind1`` and checking if its fitness is valid will give something like this

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 20-21

The individual is printed as its base class representation (here a list) and the fitness is invalid because it contains no values.

Evaluation
----------

The evaluation is the most personal part of an evolutionary algorithm, it is
the only part of the library that you must write yourself. A typical
evaluation function takes one individual as argument and return its fitness as
a :class:`tuple`. As shown in the in the :ref:`core` section, a fitness is a list of floating point values and has a
property :attr:`~deap.base.Fitness.valid` to know if this individual shall be re-evaluated. The
fitness is set by setting the :attr:`~deap.base.Fitness.values` to the
associated :class:`tuple`. For example, the following evaluates the previously created individual ``ind1`` and assign its fitness to the corresponding values.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 24-32

Dealing with single objective fitness is not different, the evaluation function **must** return a tuple because single-objective is treated as a special case of multi-objective.

Mutation
--------
The next kind of operator that we will present is the mutation operator.
There is a variety of mutation operators in the :mod:`deap.tools` module.
Each mutation has its own characteristics and may be applied to different type
of individual. Be careful to read the documentation of the selected operator
in order to avoid undesirable behaviour.

The general rule for mutation operators is that they **only** mutate, this
means that an independent copy must be made prior to mutating the individual
if the original individual has to be kept or is a *reference* to an other individual (see the selection operator).

In order to apply a mutation (here a gaussian mutation) on the individual ``ind1``,
simply apply the desired function.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 35-37

The fitness' values are deleted because they not related to the individual anymore. As stated above, the mutation does mutate and only mutate an individual it is not responsible of invalidating the fitness nor anything else. The following shows that ``ind2`` and ``mutant`` are in fact the same individual.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 39-40

Crossover
---------

The second kind of operator that we will present is the crossover operator.
There is a variety of crossover operators in the :mod:`deap.tools` module.
Each crossover has its own characteristics and may be applied to different type
of individuals. Be careful to read the documentation of the selected operator
in order to avoid undesirable behaviour.

The general rule for crossover operators is that they **only** mate individuals, this
means that an independent copies must be made prior to mating the individuals
if the original individuals have to be kept or is are *references* to other
individuals (see the selection operator).

Lets apply a crossover operation to produce the two children that are cloned beforehand.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 43-46

.. note::

	Just as a remark on the language, the form ``toolbox.clone([ind1, ind2])``
	cannot be used because if ``ind1`` and ``ind2`` are referring to the same
	location in memory (the same individual) there will be a single independent
	copy of the individual and the second one will be a reference to this same
	independent copy. This is caused by the mechanism that prevents recursive
	loops. The first time the individual is seen, it is put in the "memo"
	dictionary, the next time it is seen the deep copy stops for that object
	and puts a reference to that previously created deep copy. Care should be
	taken when deep copying containers.


Selection
---------

Selection is made among a population by the selection operators that are
available in the :mod:`deap.operators` module. The selection operator usually
takes as first argument an iterable container of individuals and the number of
individuals to select. It returns a list containing the references to the
selected individuals. The selection is made as follow.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 49-50

.. warning:: It is **very** important here to note that the selection
   operators does not duplicate any individual during the selection process. 
   If an individual is selected twice and one of either object is modified, 
   the other will also be modified. Only a reference to the individual is 
   copied. Just like every other operator it selects and only selects.

Usually duplication of the entire population will be made after selection or 
before variation.

.. literalinclude:: /code/tutorials/part_3/3_next_step.py
   :lines: 56-57


Using the Toolbox
-----------------

The toolbox is intended to contain all the evolutionary tools, from the object
initializers to the evaluation operator. It allows easy configuration of each
algorithms. The toolbox has basically two methods,
:meth:`~deap.toolbox.Toolbox.register` and
:meth:`~deap.toolbox.Toolbox.unregister`, that are used to add or remove tools
from the toolbox.

This part of the tutorial will focus on registration of the evolutionary tools
in the toolbox rather than the initialization tools. The usual names for the
evolutionary tools are :func:`~deap.mate`, :func:`~deap.mutate`,
:func:`~deap.evaluate` and :func:`~deap.select`, however, any name can be
registered as long as it is unique. Here is how they are registered in the
toolbox.

.. literalinclude:: /code/tutorials/part_3/3_6_using_the_toolbox.py
   :lines: 2-8,10-15

Using the toolbox for registering tools helps keeping the rest of the
algorithms independent from the operator set. Using this scheme makes it very
easy to locate and change any tool in the toolbox if needed.

.. _using-tools:

Using the Tools
+++++++++++++++
When building evolutionary algorithms the toolbox is used to contain the
operators, which are called using their generic name. For example, here is a
very simple generational evolutionary algorithm.

.. literalinclude:: /code/tutorials/part_3/3_6_using_the_toolbox.py
   :lines: 30-

This is a complete algorithm. It is generic enough to accept any kind of
individual and any operator, as long as the operators are suitable for the
chosen individual type. As shown in the last example, the usage of the toolbox
allows to write algorithms that are as close as possible to the pseudo code.
Now it is up to you to write and experiment your own.

Tool Decoration
+++++++++++++++
Tool decoration is a very powerful feature that helps to control very precise
thing during an evolution without changing anything in the algorithm or
operators. A decorator is a wrapper that is called instead of a function. It
is asked to make some initialization and termination work before and after the
actual function is called. For example, in the case of a constrained domain,
one can apply a decorator to the mutation and crossover in order to keep any
individual from being out-of-bound. The following defines a decorator that
checks if any attribute in the list is out-of-bound and clips it if it is the
case. The decorator is defined using three functions in order to receive the
*min* and *max* arguments. Whenever the mutation or crossover is called,
bounds will be check on the resulting individuals.

.. literalinclude:: /code/tutorials/part_3/3_6_2_tool_decoration.py
   :lines: 8-

This will work on crossover and mutation because both return a tuple of
individuals. The mutation is often considered to return a single individual
but again like for the evaluation, the single individual case is a special
case of the multiple individual case.

|more| For more information on decorators, see 
`Introduction to Python Decorators <http://www.artima.com/weblogs/viewpost.jsp?thread=240808>`_ 
and `Python Decorator Libary <http://wiki.python.org/moin/PythonDecoratorLibrary>`_.

Variations
----------
Variations allows to build simple algorithms using predefined small building blocks. In
order to use a variation, the toolbox must be set to contain the required
operators. For example in the lastly presented complete algorithm, the
crossover and mutation are regrouped in the :func:`~deap.algorithms.varAnd`
function, this function requires the toolbox to contain the :func:`~deap.mate`
and :func:`~deap.mutate` functions. The variations can be used to simplify
the writing of an algorithm as follow.

.. literalinclude:: /code/tutorials/part_3/3_7_variations.py
   :lines: 33-

This last example shows that using the variations makes it straight forward to
build algorithms that are very close to the pseudo-code.

Algorithms
----------
There is several algorithms implemented in the :mod:`~deap.algorithms` module.
They are very simple and
reflect the basic types of evolutionary algorithms present in the literature.
The algorithms use a :class:`~deap.base.Toolbox` as defined in the last
sections. In order to setup a toolbox for an algorithm, you must register the
desired operators under a specified names, refer to the documentation of the
selected algorithm for more details. Once the toolbox is ready, it is time to
launch the algorithm. The simple evolutionary algorithm takes 5 arguments, a
*population*, a *toolbox*, a probability of mating each individual at each
generation (*cxpb*), a probability of mutating each individual at each
generation (*mutpb*) and a number of generations to accomplish (*ngen*).

.. literalinclude:: /code/tutorials/part_3/3_8_algorithms.py
   :lines: 33-

The best way to understand what the simple evolutionary algorithm does, it to
take a look at the documentation or the source code

Now that you built your own evolutionary algorithm in python, you are welcome
to gives us feedback and appreciation. We would also really like to hear about
your project and success stories with DEAP.

.. |more| image:: /_images/more.png
          :align: middle
          :alt: more info

