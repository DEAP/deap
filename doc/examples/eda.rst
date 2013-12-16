=======================================
Making Your Own Strategy : A Simple EDA
=======================================

As seen in the :ref:`cma-es` example, the
:func:`~deap.algorithms.eaGenerateUpdate` algorithm is suitable for algorithms
learning the problem distribution from the population. Here we'll cover how to
implement a strategy that generates individuals based on an updated sampling
function learnt from the sampled population.

Estimation of distribution
==========================

The basic concept concept behind EDA is to sample :math:`\lambda` individuals
with a certain distribution and estimate the problem distribution from the
:math:`\mu` best individuals. This really simple concept adhere to the
generate-update logic. The strategy contains a random number generator which
is adapted from the population. The following :class:`EDA` class do just that.

.. literalinclude:: /../examples/eda/fctmin.py
   :pyobject: EDA

A normal random number generator is initialized with a certain mean
(*centroid*) and standard deviation (*sigma*) for each 
dimension. The :meth:`generate` method uses numpy to generate *lambda_*
sequences in *dim* dimensions, then the sequences are used to initialize
individuals of class given in the *ind_init* argument. Finally, the
:meth:`update` computes the average (centre) of the `mu` best individuals and
estimates the variance over all attributes of each individual. Once
:meth:`update` is called the distributions parameters are changed and a new
population can be generated.

Objects Needed
==============

Two classes are needed, a minimization fitness and a individual that will
combine the fitness and the real values. Moreover, we will use
:class:`numpy.ndarray` as base class for our individuals.

.. literalinclude:: /../examples/eda/fctmin.py
   :lines: 28-29

Operators
=========

The :func:`~deap.algorithms.eaGenerateUpdate` algorithm requires to set in a
toolbox an evaluation function, an generation method and an update method.
We will use the method of an initialized :class:`EDA`. For the generate
method, we set the class that the individuals are transferred in to our
:class:`Individual` class containing a fitness.

.. literalinclude:: /../examples/eda/fctmin.py
   :pyobject: main

The complete :example:`eda/fctmin`. 
