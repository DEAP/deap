===========
What's New?
===========
Here is a (incomplete) log of the changes made to DEAP over time. 


Release 0.7
===========
- Modified structure so that DTM is a module of DEAP.
- Restructured modules in a more permanent and coherent way.
	
  - The toolbox is now in the module base.
  - The operators have been moved to the tools module.
  - Checkpoint, Statistics, History and Hall-of-Fame are now also in the tools module.
  - Moved the GP specific operators to the gp module.
	
- Renamed some operator for coherence.
- Reintroduced a convenient, coherent and simple Statistics module.
- Changed the Milestone module name for the more common Checkpoint name.
- Eliminated the confusing *content_init* and *size_init* keywords in the toolbox.
- Refactored the whole documentation in a more structured manner.
- Added a benchmark module containing some of the most classic benchmark functions.
- Added a lots of examples again :
	
  - Differential evolution (*x2*);
  - Evolution strategy : One fifth rule;
  - *k*-nearest neighbours feature selection;
  - One Max : Multipopulation and using NumPy;
  - Particle Swarm Optimization;
  - Hillis' coevolution of sorting networks;
  - CMA-ES :math:`1+\lambda`.


Release 0.6
===========
- Operator modify in-place the individuals (simplify a lot the algorithms).
- Toolbox now contains two basic methods, map and clone that are useful in the algorithms.
- The two methods can be replaced (as usual) to modify the behaviour of the algorithms.
- Added new module History (compatible with NetworkX).
- Genetic programming is now possible with Automatically Defined Functions (ADFs).
- Algorithms now refers to literature algorithms.
- Added new examples :

  - Coevolution; 
  - Variable length genotype;
  - Multiobjective;
  - Inheriting from a Set;
  - Using ADFs;
  - Multiprocessing.

- Basic operators can now be enhanced with decorators to do all sort of funny stuff.

Release 0.5
===========
- Added a new module Milestone.
- Enhanced Fitness efficiency when comparing fitnesses.
- Replaced old base types with python built-in types.
- Added an example of deriving from sets.
- Added SPEA-II algorithm.
- Fitnesses are no more extended when assigning value, the values are simply assigned.