=========================
One Max Genetic Algorithm
=========================

This is the first complete program built with EAP. It will help new users to overview some of the possibilities in EAP. The problem is very simple, we search for a 1 filled list individual. This problem is widely used in the evolutionary computation community since it is very simple and it illutrates well the potential of evolutionary algorithms.

Setting it up
=============

Here we use the one max problem to show how simple can be an evolutionary algorithm with EAP. The first thing to do is to ellaborate the structures of the algorithm. It is pretty obvious in this case that a :class:`~eap.base.ListIndividual` is probably the most interesting kind of individual available. In order to limit the domain of the problem, the attributes of the individual will be :class:`booleans`. A :class:`~eap.base.ListPopulation` will alose probably do everyting that is needed for this problem.

In order to set this up, we will need to import the :mod:`eap.base` module and to facilitate our labor the :mod:`eap.creator` module.

.. literalinclude:: ../src/examples/ga_onemax.py
   :lines: 22-23
   
Then we need to create the :class:`~eap.creator.Creator` and add some builder methods for the fitnesses, the individuals and the population.

.. literalinclude:: ../src/examples/ga_onemax.py
   :lines: 30-36

The last lines create a :class:`~eap.base.Fitness` that has to be maximized, a :class:`~eap.base.ListIndividual` that has for fitness the maximizing fitness and attribute generator a :func:`~eap.base.booleanGenerator` and a :class:`~eap.base.ListPopulation` that will be filled with the :class:`~eap.base.ListIndividual`\ s.

More to come soon...

The complete `ga_onemax <http://peace.kenai.com/ga_onemax.py>`_ code.