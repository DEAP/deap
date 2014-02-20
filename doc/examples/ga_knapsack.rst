=====================================
Knapsack Problem: Inheriting from Set
=====================================

Again for this example we will use a very simple problem, the 0-1 Knapsack.
The purpose of this example is to show the simplicity of DEAP and the ease to
inherit from anyting else than a simple list or array.

Many evolutionary algorithm textbooks mention that the best way to have an
efficient algorithm to have a representation close the problem. Here, what can
be closer to a bag than a set? Lets make our individuals inherit from the
:class:`set` class.

.. literalinclude:: /../examples/ga/knapsack.py
   :lines: 41-42

That's it. You now have individuals that are in fact sets, they have the usual
attribute :attr:`fitness`. The fitness is a
minimization of the first objective (the weight of the bag) and a maximization
of the second objective (the value of the bag). We will now create a
dictionary of 100 random items to map the values and weights. 

.. literalinclude:: /../examples/ga/knapsack.py
   :lines: 34-39

We now need to initialize a population and the individuals therein. For this
we will need a :class:`~deap.base.Toolbox` to register our generators since
sets can also be created with an input iterable. 

.. literalinclude:: /../examples/ga/knapsack.py
   :lines: 44,47,50-53

Voilà! The *last* thing to do is to define our evaluation function.

.. literalinclude:: /../examples/ga/knapsack.py
   :pyobject: evalKnapsack

Everything is ready for evolution. Ho no wait, since DEAP's developers are
lazy, there is no crossover and mutation operators that can be applied
directly on sets. Lets define some. For example, a crossover, producing two 
children from two parents, could be that the first child is the
intersection of the two sets and the second child their absolute difference.

.. literalinclude:: /../examples/ga/knapsack.py
   :pyobject: cxSet

A mutation operator could randomly add or remove an element from the set
input individual. 

.. literalinclude:: /../examples/ga/knapsack.py
   :pyobject: mutSet


We then register these operators in the toolbox. Since it is a multi-objective
problem, we have selected the SPEA-II selection scheme : 
:func:`~deap.tools.selSPEA2`

.. literalinclude:: /../examples/ga/knapsack.py
   :lines: 83-86

From here, everything left to do is either write the algorithm or use 
provided in :mod:`~deap.algorithms`. Here we will use the 
:func:`~deap.algorithms.eaMuPlusLambda` algorithm.

.. literalinclude:: /../examples/ga/knapsack.py
   :lines: 88,90-107

Finally, a :class:`~deap.tools.ParetoFront` may be used to retrieve the best
non dominated individuals of the evolution and a
:class:`~deap.tools.Statistics` object is created for compiling four
different statistics over the generations. The Numpy functions are registered
in the statistics object with the ``axis=0`` argument to compute the
statistics on each objective independently. Otherwise, Numpy would compute
a single mean for both objectives.

The complete :example:`ga/knapsack`.
