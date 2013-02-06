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

.. literalinclude:: /code/examples/coev/coev_coop_evol.py
   :lines: 74

Cooperative coevolution works by sending the best individual of each species
(called representative) to help in the evaluation of the individuals of the
other species. Since the individuals are not yet evaluated we select randomly
the individuals that will be in the set of representatives. 

.. literalinclude:: /code/examples/coev/coev_coop_evol.py
   :lines: 79

The evaluation function takes a list of individuals to be evaluated including
the representatives of the other species and possibly some other arguments.
It is not presented in detail for scope reasons, the structure would be, as
usual, something like this ::

   def evaluate(individuals):
       # Compute the collaboration fitness
       return fitness,

The evolution can now begin.

.. literalinclude:: /code/examples/coev/coev_coop_evol.py
   :lines: 87-99,105-107,115

The last lines evolve each species once before sharing their representatives.
The common parts of an evolutionary algorithm are all present, variation,
evaluation and selection occurs for each species. The species index is simply
a unique number identifying each species, it can be used to keep independent
statistics on each new species added.

After evolving each species, steps described in [Potter2001]_ are achieved
to add a species and remove useless species on stagnation. These steps are not
covered in this example but are present in the complete source code of
the coevolution examples.

- `Coevolution Base <code/coev/coev_coop_base.py>`_
- `Coevolution Niching <code/coev/coev_coop_niche.py>`_
- `Coevolution Generalization <code/coev/coev_coop_gen.py>`_
- `Coevolution Adaptation <code/coev/coev_coop_adapt.py>`_
- `Coevolution Final <code/coev/coev_coop_evol.py>`_
       
.. [Potter2001] Potter, M. and De Jong, K., 2001, Cooperative
   Coevolution: An Architecture for Evolving Co-adapted Subcomponents.
