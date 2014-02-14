Moving Peaks Benchmark with Multiswarm PSO
==========================================
In this example we show how to use the :class:`~deap.benchmarks.movingpeaks.MovingPeaks` benchmark. A popular algorithm on this benchmark is the Multiswarm PSO (MPSO) [Blackwell2004]_ which achieve a great offline error and is able to follow multiple peaks at the same time.

Choosing the Scenario
---------------------
The moving peak benchmark allows to choose from the 3 original scenarios proposed in the `original studies <http://people.aifb.kit.edu/jbr/MovPeaks/>`_. This is done by retreiving one of the constants defined in the :mod:`~deap.benchmarks.movingpeaks` module. Here we will use Scenario 2.

.. literalinclude:: /../examples/pso/multiswarm.py
   :lines: 37,41

Once the scenario is retrieved, we need to set a few more constants and instantiate the benchmark, here the number of dimensions and the bounds of the problem.

.. literalinclude:: /./examples/pso/multiswarm.py
   :lines: 43-46

For a list of all the variables defined in the ``SENARIO_X`` dictionaries see :class:`~deap.benchmarks.movingpeaks.MovingPeaks` class documentation.

Initialization
--------------
As in every DEAP example we are required to create the objects. The moving peak benchmark is a max problem, thus we need a maximizing fitness. And, we associate that fitness to a particle as in the :doc:`pso_basic` example.

.. literalinclude:: /../examples/pso/multiswarm.py
   :lines: 48-51

Then, the particle generator is defined. It takes the particle class object :data:`pclass` into which to put the data. Remeber that :class:`creator.Particle`, which is gonna be give to this argument in the toolbox, inherits from :class:`list` and can be initialized with an iterable. The position (elements of the list) and the speed (attribute) of the particle is set to randomly generated numbers between the given bounds.

.. literalinclude:: /../examples/pso/multiswarm.py
   :pyobject: generate

The next function update the particle position and speed.

.. literalinclude:: /../examples/pso/multiswarm.py
   :pyobject: updateParticle

Thereafter, a function "converting" a particle to a quantum particle with different possible distributions is defined.

.. literalinclude:: /../examples/pso/multiswarm.py
   :pyobject: convertQuantum

Finally, all the functions are registered in the toolbox for further use in the algorithm.

.. literalinclude:: /../examples/pso/multiswarm.py
   :lines: 97-104

Moving Peaks
------------
The registered evaluation function in the toolbox refers directly to the instance of the :class:`~deap.benchmarks.movingpeaks.MovingPeaks` benchmark object :data:`mpb`. The call to :func:`mpb` evaluates the given individuals as any other evaluation function.

Algorithm
---------
The algorithm is fully detailed in the file :example:`pso/multiswarm`, it reflects what is described in [Blackwell2004]_.

.. [Blackwell2004] Blackwell, T., & Branke, J. (2004). Multi-swarm optimization in dynamic environments. In *Applications of Evolutionary Computing* (pp. 489-500). Springer Berlin Heidelberg.