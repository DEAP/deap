Extensions to the Algorithms
============================

Here are presented more tools that can be used in the algorithms.

Statistics
----------

Hall of Fame
------------

.. autoclass:: eap.operators.HallOfFame

   .. automethod:: eap.operators.HallOfFame.update
   
   .. automethod:: eap.operators.HallOfFame.insert
   
   .. automethod:: eap.operators.HallOfFame.remove
   
   .. automethod:: eap.operators.HallOfFame.clear

.. autoclass:: eap.operators.ParetoFront([similar])

   .. automethod:: eap.operators.ParetoFront.update

Milestone
---------

.. autoclass:: eap.operators.Milestone([yaml,object[, ...]])
   
   .. automethod:: eap.operators.Milestone.dump(prefix)
   
   .. automethod:: eap.operators.Milestone.load(filename)
   
   .. automethod:: eap.operators.Milestone.add(object[, ...])
   
   .. automethod:: eap.operators.Milestone.remove(object[, ...])

History
-------

.. autoclass:: eap.operators.History
   
   .. automethod:: eap.operators.History.populate
   
   .. automethod:: eap.operators.History.update(individual[, ...])
   
   .. autoattribute:: eap.operators.History.decorator