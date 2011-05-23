Extensions to the Algorithms
============================

Here are presented more tools that can be used in the algorithms.

Statistics
----------

Hall of Fame
------------

.. autoclass:: deap.operators.HallOfFame

   .. automethod:: deap.operators.HallOfFame.update
   
   .. automethod:: deap.operators.HallOfFame.insert
   
   .. automethod:: deap.operators.HallOfFame.remove
   
   .. automethod:: deap.operators.HallOfFame.clear

.. autoclass:: deap.operators.ParetoFront([similar])

   .. automethod:: deap.operators.ParetoFront.update

Milestone
---------

.. autoclass:: deap.operators.Milestone([yaml,object[, ...]])
   
   .. automethod:: deap.operators.Milestone.dump(prefix)
   
   .. automethod:: deap.operators.Milestone.load(filename)
   
   .. automethod:: deap.operators.Milestone.add(object[, ...])
   
   .. automethod:: deap.operators.Milestone.remove(object[, ...])

History
-------

.. autoclass:: deap.operators.History
   
   .. automethod:: deap.operators.History.populate
   
   .. automethod:: deap.operators.History.update(individual[, ...])
   
   .. autoattribute:: deap.operators.History.decorator