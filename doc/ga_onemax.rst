=========================
One Max Genetic Algorithm
=========================

This is the first complete program built with EAP. It will help new users to overview some of the possibilities in EAP. The problem is very simple, we search for a 1 filled list individual. This problem is widely used in the evolutionary computation community since it is very simple and it illutrates well the potential of evolutionary algorithms.

Setting It Up
=============

Here we use the one max problem to show how simple can be an evolutionary algorithm with EAP. The first thing to do is to ellaborate the structures of the algorithm. It is pretty obvious in this case that a :class:`~eap.base.ListIndividual` is probably the most interesting kind of individual available. In order to limit the domain of the problem, the attributes of the individual will be :class:`booleans`. A :class:`~eap.base.ListPopulation` will alose probably do everyting that is needed for this problem.

In order to set this up, we will need to import the :mod:`eap.base` module and to facilitate our labor the :mod:`eap.creator` module.

.. literalinclude:: ../src/examples/ga_onemax.py
   :lines: 23-24
   
Then we need to create a :class:`~eap.toolbox.Toolbox` and add some builder methods for the fitnesses, the individuals and the population.

.. literalinclude:: ../src/examples/ga_onemax.py
   :lines: 28-33

The last lines create a :class:`~eap.base.Fitness` that has to be maximized, an :class:`~eap.base.Individual` that has for fitness the maximizing fitness and attribute generator a :func:`~eap.base.booleanGenerator` and a :class:`~eap.base.Population` that will be filled with :class:`~eap.base.Individual` instances.

The Evaluation Function
=======================

The evaluation function is pretty simple in this case, we need to count the number of :data:`True` in the individual and append this value to the fitness. This is done by the following lines of code.

.. literalinclude:: ../src/examples/ga_onemax.py
   :lines: 35-37
   
The Genetic Operators
=====================

There is two way of using operators, the first one, is to simply call the function from the :mod:`eap.toolbox` module and the second one is to register them with their argument in the a :class:`~eap.toolbox.Toolbox`. The most convenient way is to register them in the toolbox, because it allows to easily switch between operators if desired. The toolbox method is also used in the algorithms (that are shown in the :ref:`short version <short-ga-onemax>`)

Registering the operators in the toolbox is very simple.

.. literalinclude:: ../src/examples/ga_onemax.py
   :lines: 39-42

The Evolution
=============

The complete `ga_onemax <http://peace.kenai.com/ga_onemax.py>`_ code.