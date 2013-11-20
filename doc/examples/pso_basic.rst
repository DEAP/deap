==================================
Particle Swarm Optimization Basics
==================================

The implementation presented here is the original PSO algorithm as presented
in [Poli2007]_. From Wikipedia definition of PSO

    `PSO optimizes a problem by having a population of candidate solutions,
    here dubbed particles, and moving these particles around in the
    search-space according to simple mathematical formulae. The movements of
    the particles are guided by the best found positions in the search-space
    which are updated as better positions are found by the particles.`

Modules
=======

Before writing functions and algorithms, we need to import some module from
the standard library and from DEAP.

.. literalinclude:: /../examples/pso/basic.py
   :lines: 16-24

Representation
==============

The particle's goal is to maximize the return value of the fonction at its
position.

PSO particles are essentially described as a positions in a search-space of D
dimensions. Each particle also has a vector representing the speed of the
particle in each dimension. Finally, each particle keeps a reference to the
best state in which it has been so far.

This translates in DEAP by the following two lines of code :

.. literalinclude:: /../examples/pso/basic.py
   :lines: 26-28

Here we create two new objects in the :mod:`~deap.creator` space. First, we
create a :class:`FitnessMax` object, and we specify the
:attr:`~deap.base.Fitness.weights` to be ``(1.0,)``, this means we want to
maximise the value of the fitness of our particles. The second object we
create represent our particle. We defined it as a :class:`list` to which we
add five attributes. The first attribute is the fitness of the particle, the
second is the speed of the particle which is also goind to be a list, the
third and fourth are the limit of the speed value, and the fifth attribute
will be a reference to a copy of the best state the particle has been so far.
Since the particle has no final state until at has been evaluated, the
reference is set to ``None``. The speed limits are also set to ``None`` to
allow configuration via the function :func:`generate` presented in the next
section.

Operators
=========

PSO original algorithm use three operators : initializer, updater and
evaluator. The initialization consist in generating a random position and a
random speed for a particle. The next function create a particle and
initialize its attributes, except for the attribute :attr:`best`, which will
be set only after evaluation :

.. literalinclude:: /../examples/pso/basic.py
   :pyobject: generate

The function :func:`updateParticle` first computes the speed, then limits the
speed values between ``smin`` and ``smax``, and finally computes the new
particle position.

.. literalinclude:: /../examples/pso/basic.py
   :pyobject: updateParticle

The operators are registered in the toolbox with their parameters. The
particle value at the beginning are in the range ``[-100, 100]``
(:attr:`pmin` and :attr:`pmax`), and the speed is limited in the range
``[-50, 50]`` through all the evolution.

The evaluation function :func:`~deap.benchmarks.h1` is from [Knoek2003]_. The
function is already defined in the benchmarks module, so we can register it
directly.

.. literalinclude:: /../examples/pso/basic.py
   :lines: 50-54

Algorithm
=========

Once the operators are registered in the toolbox, we can fire up the
algorithm by firstly creating a new population, and then apply the original
PSO algorithm. The variable `best` contains the best particle ever found (it
known as gbest in the original algorithm).

.. literalinclude:: /../examples/pso/basic.py
   :pyobject: main

Conclusion
==========

The full PSO basic example can be found here : :example:`pso/basic`.

This is a video of the algorithm in action, plotted with matplotlib_. 
The red dot represents the best solution found so far.

.. _matplotlib: http://matplotlib.org/

.. raw:: html

	<center>
	<object style="height: 390px; width: 640px">
	<param name="movie" value="http://www.youtube.com/v/f3MW2krobpo?version=3&feature=player_detailpage">
	<param name="allowFullScreen" value="true">
	<param name="allowScriptAccess" value="always">
	<embed src="http://www.youtube.com/v/f3MW2krobpo?version=3&feature=player_detailpage" 
		   type="application/x-shockwave-flash" allowfullscreen="true" 
		   allowScriptAccess="always" 
		   width="640" height="360">
	</object>
	</center>

References
==========

.. [Poli2007] Ricardo Poli, James Kennedy and Tim Blackwell, "Particle swarm optimization an overview". Swarm Intelligence. 2007; 1: 33–57
.. [Knoek2003] Arthur J. Knoek van Soest and L. J. R. Richard Casius, "The merits of a parallel genetic algorithm in solving hard optimization problems". Journal of Biomechanical Engineering. 2003; 125: 141–146



