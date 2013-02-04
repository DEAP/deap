.. _core:

Core Architecture
=================
The core architecture of DEAP is composed of two simple structures, the
:mod:`~deap.creator` and the :class:`~deap.base.toolbox`. The former provides
structuring capabilities, while the latter adds genericity potential to every
algorithm. Both structures are described in detail in the following sections.

Creator
-------
.. automodule:: deap.creator

.. autofunction:: deap.creator.create(name, base[, attribute[, ...]])

.. autodata:: deap.creator.class_replacers

Toolbox
-------
The :class:`Toolbox` is a container for the tools that are selected by the
user. The toolbox is manually populated with the desired tools that best apply
with the chosen representation and algorithm from the user's point of view.
This way it is possible to build algorithms that are totally decoupled from
the operator set, as one only need to update the toolbox in order to make the
algorithm run with a different operator set as the algorithms are built to use
aliases instead of direct function names.

.. autoclass:: deap.base.Toolbox
	
	.. automethod:: deap.base.Toolbox.register(alias, method[, argument[, ...]])
	
	.. automethod:: deap.base.Toolbox.unregister(alias)
	
	.. automethod:: deap.base.Toolbox.decorate(alias, decorator[, decorator[, ...]])

Fitness
-------
.. autoclass:: deap.base.Fitness([values])
	:members: