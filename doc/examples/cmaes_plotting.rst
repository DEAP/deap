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
The general evolution loop of function :func:`~deap.algorithms.eaGenerateUpdate`
is somewhat insufficient for our purpose. We need to gather the required data
on each generation. So instead of using the  :func:`~deap.algorithms.eaGenerateUpdate`
function, we'll develop it to get a grip on what is recorded.

The beginning of this example is exactly the same as the :ref:`CMA-ES <cma-es>`
