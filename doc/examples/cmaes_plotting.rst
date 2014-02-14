=====================================================
Plotting Important Data: Visualizing the CMA Strategy
=====================================================
With this example we show one technique for plotting the data of an evolution.
As developpers of DEAP we cannot make a choice on what data is important to
plot and this part is left to the user. Although, plotting would all occur the
same way. First the data is gathered during the evolution and at the end the
figures are created from the data. This model is the simplest possible. One
could also write all data to a file and read those file again to plot the
figures. This later model would be more fault tolerant as if the evolution
does not terminate normally, the figures could still be plotted. But, we want
to keep this example as simpe as possible and thus we will present the former
model.

Evolution Loop
==============
The beginning of this example is exactly the same as the :ref:`CMA-ES
<cma-es>` example. The general evolution loop of function
:func:`~deap.algorithms.eaGenerateUpdate` is somewhat insufficient for our
purpose. We need to gather the required data on each generation. So instead of
using the  :func:`~deap.algorithms.eaGenerateUpdate` function, we'll develop
it to get a grip on what is recorded. First, we'll create objects to record
our data. Here we want to plot, in addition to what the
:class:`~deap.tools.Logbook` and :class:`~deap.tools.HallOfFame` objects contain, the
step size, the axis ratio and the major axis of the covariace matrix, the best
value so far, the best coordinates so far and the standard deviation of the
all coordinates at each generation.

.. literalinclude:: /../examples/es/cma_plotting.py
   :lines: 59-64

Once the objects are created, the evolution loop, based on a generational
stopping criterion, calls repeatedly the :meth:`generate`, :meth:`evaluate`
and :meth:`update` methods registered in the toolbox.

.. literalinclude:: /../examples/es/cma_plotting.py
   :lines: 66-75

Then, the previoulsy created objects start to play their role. The
data is recorded in each object on each generation.

.. literalinclude:: /../examples/es/cma_plotting.py
   :lines: 88-93

Now that the data is recorded the only thing left to do is to plot it. We'll
use `matplotlib <http://matplotlib.org>`_ to generate the graphics from the
recorded data.

.. literalinclude:: /../examples/es/cma_plotting.py
   :lines: 95-124

Which gives the following result.

.. plot:: ../examples/es/cma_plotting.py
   :width: 67%