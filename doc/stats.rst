==========
Statistics
==========

Observable Objects
==================

.. automodule:: eap.observable

.. autoclass:: Observable
   :members: suscribe, unsuscribe
   
   .. automethod:: emit(output)

Statistics Generators
=====================

.. automodule:: eap.stats

.. function:: eap.stats.getStats(statsName)

   Return the current statistics that are associated with *statsName*. Usually, *statsName* is the name of the :class:`~observable.Observable` suscribed generator function.

.. function:: eap.stats.pushStats(statsName, stats)

   Write the *stats* in the *statsName* entry of the dictionary, every push with the same name will replace the current value.

.. autoclass:: eap.stats.Stats