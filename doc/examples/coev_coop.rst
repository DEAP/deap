=======================
Cooperative Coevolution
=======================

This example explores cooperative coevolution using DEAP. This tutorial is not
as complete as previous examples concerning type creation and other
basic stuff. Instead, we cover the concepts of coevolution as they would be
applied in DEAP. Assume that if a function from the toolbox is used,
it has been properly registered. This example makes a great template for
implementing your own coevolutionary algorithm, it is based on the description
of cooperative coevolution by [Potter2001]_.

Coevolution is, in fact, just an extension of how algorithms works in deap.
Multiple populations are evolved in turn (or simultaneously on multiple
processors) just like in traditional genetic algorithms. The implementation of
the coevolution is thus straightforward. A first loop acts for iterating over
the populations and a second loop iterates over the individuals of these
population.

The first step is to create a bunch of species that will evolve in our
population.

.. literalinclude:: /../examples/coev/coop_evol.py
   :lines: 72

Cooperative coevolution works by sending the best individual of each species
(called representative) to help in the evaluation of the individuals of the
other species. Since the individuals are not yet evaluated we select randomly
the individuals that will be in the set of representatives. 

.. literalinclude:: /../examples/coev/coop_evol.py
   :lines: 77

The evaluation function takes a list of individuals to be evaluated including
the representatives of the other species and possibly some other arguments.
It is not presented in detail for scope reasons, the structure would be, as
usual, something like this ::

   def evaluate(individuals):
       # Compute the collaboration fitness
       return fitness,

The evolution can now begin.

.. literalinclude:: /../examples/coev/coop_evol.py
   :lines: 85-96,103-106,113-114

The last lines evolve each species once before sharing their representatives.
The common parts of an evolutionary algorithm are all present, variation,
evaluation and selection occurs for each species. The species index is simply
a unique number identifying each species, it can be used to keep independent
statistics on each new species added.

After evolving each species, steps described in [Potter2001]_ are achieved
to add a species and remove useless species on stagnation. These steps are not
covered in this example but are present in the complete source code of
the coevolution examples.

- :example:`Coevolution Base <coev/coop_base>`
- :example:`Coevolution Niching <coev/coop_niche>`
- :example:`Coevolution Generalization <coev/coop_gen>`
- :example:`Coevolution Adaptation <coev/coop_adapt>`
- :example:`Coevolution Final <coev/coop_evol>`
       
.. [Potter2001] Potter, M. and De Jong, K., 2001, Cooperative
   Coevolution: An Architecture for Evolving Co-adapted Subcomponents.
