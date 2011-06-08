Creating Types
==============
This tutorial shows how types are created using the creator.

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

Genetic Algorithm
-----------------

Genetic Programming
-------------------
