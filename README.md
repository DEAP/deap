# DEAP

DEAP is a novel evolutionary computation framework for rapid prototyping and testing of 
ideas. It seeks to make algorithms explicit and data structures transparent. It works in perfect harmony with parallelisation mechanism such as multiprocessing and [SCOOP](http://scoop.googlecode.com).

DEAP includes the following features:

  * Genetic algorithm using any imaginable representation
    * List, Array, Set, Dictionary, Tree, Numpy Array, etc.
  * Genetic programing using prefix trees
    * Loosely typed, Strongly typed
    * Automatically defined functions
  * Evolution strategies (including CMA-ES)
  * Multi-objective optimisation (NSGA-II, SPEA-II)
  * Co-evolution (cooperative and competitive) of multiple populations
  * Parallelization of the evaluations (and more)
  * Hall of Fame of the best individuals that lived in the population
  * Checkpoints that take snapshots of a system regularly
  * Benchmarks module containing most common test functions
  * Genealogy of an evolution (that is compatible with [NetworkX](http://networkx.lanl.gov))
  * Examples of alternative algorithms : Particle Swarm Optimization, Differential Evolution, Estimation of Distribution Algorithm

## Downloads

Following acceptation of [PEP 438](http://www.python.org/dev/peps/pep-0438/) by the Python community, we have moved DEAP's source releases on [PyPI](https://pypi.python.org).

You can find the most recent releases at: https://pypi.python.org/pypi/deap/.

## Documentation
See the [DEAP User's Guide](http://deap.readthedocs.org/en/1.0.x/) for DEAP documentation.

In order to get the tip documentation, change directory to the `doc` subfolder and type in `make html`, the documentation will be under `_build/html`. You will need [Sphinx](http://sphinx.pocoo.org) to build the documentation.

### Notebooks
Also checkout our new [notebook examples](https://github.com/DEAP/notebook). Using [IPython's](http://ipython.org/) notebook feature you'll be able to navigate and execute each block of code individually and fell what every line is doing. Either, look at the notebooks online using the notebook viewer links at the botom of the page or download the notebooks, navigate to the you download directory and run

```bash
ipython notebook --pylab inline
```

## Installation
We encourage you to use easy_install or pip to install DEAP on your system. Other installation procedure like apt-get, yum, etc. usually provide an outdated version.

```bash
pip install deap
```

If you wish to build from sources, download or clone the repository and type

```bash
python setup.py install
```

## Requirements
The most basic features of DEAP requires Python2.6. In order to combine the toolbox and the multiprocessing module Python2.7 is needed for its support to pickle partial functions. CMA-ES requires Numpy, and we recommend matplotlib for visualization of results as it is fully compatible with DEAP's API.

Since version 0.8, DEAP is compatible out of the box with Python 3. The installation procedure automatically translates the source to Python 3 with 2to3.

## Example

The following code gives a quick overview how simple it is to implement the Onemax problem optimization with genetic algorithm using DEAP.  More examples are provided [here](http://deap.gel.ulaval.ca/doc/default/examples/index.html).

```python
import array, random
from deap import creator, base, tools, algorithms

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMax)

toolbox = base.Toolbox()

toolbox.register("attr_bool", random.randint, 0, 1)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, 100)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evalOneMax(individual):
    return sum(individual),

toolbox.register("evaluate", evalOneMax)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

population = toolbox.population(n=300)

NGEN=40
for gen in range(NGEN):
    offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
    fits = toolbox.map(toolbox.evaluate, offspring)
    for fit, ind in zip(fits, offspring):
        ind.fitness.values = fit
    population = offspring
```

## How to cite DEAP
Authors of scientific papers including results generated using DEAP are encouraged to cite the following paper.

```xml
@article{DEAP_JMLR2012, 
    author    = " F\'elix-Antoine Fortin and Fran\c{c}ois-Michel {De Rainville} and Marc-Andr\'e Gardner and Marc Parizeau and Christian Gagn\'e ",
    title     = { {DEAP}: Evolutionary Algorithms Made Easy },
    pages    = { 2171--2175 },
    volume    = { 13 },
    month     = { jul },
    year      = { 2012 },
    journal   = { Journal of Machine Learning Research }
}
```

## Publications on DEAP

  * François-Michel De Rainville, Félix-Antoine Fortin, Marc-André Gardner, Marc Parizeau and Christian Gagné, "DEAP -- Enabling Nimbler Evolutions", SIGEVOlution, vol. 6, no 2, pp. 17-26, February 2014. [Paper](http://goo.gl/tOrXTp)
  * Félix-Antoine Fortin, François-Michel De Rainville, Marc-André Gardner, Marc Parizeau and Christian Gagné, "DEAP: Evolutionary Algorithms Made Easy", Journal of Machine Learning Research, vol. 13, pp. 2171-2175, jul 2012. [Paper](http://goo.gl/amJ3x)
  * François-Michel De Rainville, Félix-Antoine Fortin, Marc-André Gardner, Marc Parizeau and Christian Gagné, "DEAP: A Python Framework for Evolutionary Algorithms", in !EvoSoft Workshop, Companion proc. of the Genetic and Evolutionary Computation Conference (GECCO 2012), July 07-11 2012. [Paper](http://goo.gl/pXXug)

## Projects using DEAP

  * Macret, M. and Pasquier, P. (2013). Automatic Tuning of the OP-1 Synthesizer Using a Multi-objective Genetic Algorithm. In Proceedings of the 10th Sound and Music Computing Conference (SMC). (pp 614-621).
  * Fortin, F. A., Grenier, S., & Parizeau, M. (2013, July). Generalizing the improved run-time complexity algorithm for non-dominated sorting. In Proceeding of the fifteenth annual conference on Genetic and evolutionary computation conference (pp. 615-622). ACM.
  * Fortin, F. A., & Parizeau, M. (2013, July). Revisiting the NSGA-II crowding-distance computation. In Proceeding of the fifteenth annual conference on Genetic and evolutionary computation conference (pp. 623-630). ACM.
  * Marc-André Gardner, Christian Gagné, and Marc Parizeau. Estimation of Distribution Algorithm based on Hidden Markov Models for Combinatorial Optimization. in Comp. Proc. Genetic and Evolutionary Computation Conference (GECCO 2013), July 2013.
  * J. T. Zhai, M. A. Bamakhrama, and T. Stefanov. "Exploiting Just-enough Parallelism when Mapping Streaming Applications in Hard Real-time Systems". Design Automation Conference (DAC 2013), 2013.
  * V. Akbarzadeh, C. Gagné, M. Parizeau, M. Argany, M. A Mostafavi, "Probabilistic Sensing Model for Sensor Placement Optimization Based on Line-of-Sight Coverage", Accepted in IEEE Transactions on Instrumentation and Measurement, 2012.
  * M. Reif, F. Shafait, and A. Dengel. "Dataset Generation for Meta-Learning". Proceedings of the German Conference on Artificial Intelligence (KI'12). 2012. 
  * M. T. Ribeiro, A. Lacerda, A. Veloso, and N. Ziviani. "Pareto-Efficient Hybridization for Multi-Objective Recommender Systems". Proceedings of the Conference on Recommanders Systems (!RecSys'12). 2012.
  * M. Pérez-Ortiz, A. Arauzo-Azofra, C. Hervás-Martínez, L. García-Hernández and L. Salas-Morera. "A system learning user preferences for multiobjective optimization of facility layouts". Pr,oceedings on the Int. Conference on Soft Computing Models in Industrial and Environmental Applications (SOCO'12). 2012.
  * Lévesque, J.C., Durand, A., Gagné, C., and Sabourin, R., Multi-Objective Evolutionary Optimization for Generating Ensembles of Classifiers in the ROC Space, Genetic and Evolutionary Computation Conference (GECCO 2012), 2012.
  * Marc-André Gardner, Christian Gagné, and Marc Parizeau, "Bloat Control in Genetic Programming with Histogram-based Accept-Reject Method", in Proc. Genetic and Evolutionary Computation Conference (GECCO 2011), 2011.
  * Vahab Akbarzadeh, Albert Ko, Christian Gagné, and Marc Parizeau, "Topography-Aware Sensor Deployment Optimization with CMA-ES", in Proc. of Parallel Problem Solving from Nature (PPSN 2010), Springer, 2010.
  * DEAP is also used in ROS as an optimization package http://www.ros.org/wiki/deap.
  * DEAP is an optional dependency for [PyXRD](https://github.com/mathijs-dumon/PyXRD), a Python implementation of the matrix algorithm developed for the X-ray diffraction analysis of disordered lamellar structures.

If you want your project listed here, send us a link and a brief description and we'll be glad to add it.
