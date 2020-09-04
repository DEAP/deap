# DEAP

[![Build status](https://travis-ci.org/DEAP/deap.svg?branch=master)](https://travis-ci.org/DEAP/deap) [![Download](https://img.shields.io/pypi/dm/deap.svg)](https://pypi.python.org/pypi/deap) [![Join the chat at https://gitter.im/DEAP/deap](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/DEAP/deap?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![Build Status](https://dev.azure.com/fderainville/DEAP/_apis/build/status/DEAP.deap?branchName=master)](https://dev.azure.com/fderainville/DEAP/_build/latest?definitionId=1&branchName=master) [![Documentation Status](https://readthedocs.org/projects/deap/badge/?version=master)](https://deap.readthedocs.io/en/master/?badge=master)

DEAP is a novel evolutionary computation framework for rapid prototyping and testing of 
ideas. It seeks to make algorithms explicit and data structures transparent. It works in perfect harmony with parallelisation mechanisms such as multiprocessing and [SCOOP](https://github.com/soravux/scoop).

DEAP includes the following features:

  * Genetic algorithm using any imaginable representation
    * List, Array, Set, Dictionary, Tree, Numpy Array, etc.
  * Genetic programing using prefix trees
    * Loosely typed, Strongly typed
    * Automatically defined functions
  * Evolution strategies (including CMA-ES)
  * Multi-objective optimisation (NSGA-II, NSGA-III, SPEA2, MO-CMA-ES)
  * Co-evolution (cooperative and competitive) of multiple populations
  * Parallelization of the evaluations (and more)
  * Hall of Fame of the best individuals that lived in the population
  * Checkpoints that take snapshots of a system regularly
  * Benchmarks module containing most common test functions
  * Genealogy of an evolution (that is compatible with [NetworkX](https://github.com/networkx/networkx))
  * Examples of alternative algorithms : Particle Swarm Optimization, Differential Evolution, Estimation of Distribution Algorithm

## Downloads

Following acceptance of [PEP 438](http://www.python.org/dev/peps/pep-0438/) by the Python community, we have moved DEAP's source releases on [PyPI](https://pypi.python.org).

You can find the most recent releases at: https://pypi.python.org/pypi/deap/.

## Documentation
See the [DEAP User's Guide](http://deap.readthedocs.org/) for DEAP documentation.

In order to get the tip documentation, change directory to the `doc` subfolder and type in `make html`, the documentation will be under `_build/html`. You will need [Sphinx](http://sphinx.pocoo.org) to build the documentation.

### Notebooks
Also checkout our new [notebook examples](https://github.com/DEAP/notebooks). Using [Jupyter notebooks](http://jupyter.org)  you'll be able to navigate and execute each block of code individually and tell what every line is doing. Either, look at the notebooks online using the notebook viewer links at the botom of the page or download the notebooks, navigate to the you download directory and run

```bash
jupyter notebook
```

## Installation
We encourage you to use easy_install or pip to install DEAP on your system. Other installation procedure like apt-get, yum, etc. usually provide an outdated version.
```bash
pip install deap
```

The latest version can be installed with 
```bash
pip install git+https://github.com/DEAP/deap@master
```

If you wish to build from sources, download or clone the repository and type

```bash
python setup.py install
```

## Build Status
DEAP build status is available on Travis-CI https://travis-ci.org/DEAP/deap.

## Requirements
The most basic features of DEAP requires Python2.6. In order to combine the toolbox and the multiprocessing module Python2.7 is needed for its support to pickle partial functions. CMA-ES requires Numpy, and we recommend matplotlib for visualization of results as it is fully compatible with DEAP's API.

Since version 0.8, DEAP is compatible out of the box with Python 3. The installation procedure automatically translates the source to Python 3 with 2to3.

## Example

The following code gives a quick overview how simple it is to implement the Onemax problem optimization with genetic algorithm using DEAP.  More examples are provided [here](http://deap.readthedocs.org/en/master/examples/index.html).

```python
import random
from deap import creator, base, tools, algorithms

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

toolbox.register("attr_bool", random.randint, 0, 1)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, n=100)
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
    population = toolbox.select(offspring, k=len(population))
top10 = tools.selBest(population, k=10)
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
  * Ribaric, T., & Houghten, S. (2017, June). Genetic programming for improved cryptanalysis of elliptic curve cryptosystems. In 2017 IEEE Congress on Evolutionary Computation (CEC) (pp. 419-426). IEEE.
  * Ellefsen, Kai Olav, Herman Augusto Lepikson, and Jan C. Albiez. "Multiobjective coverage path planning: Enabling automated inspection of complex, real-world structures." Applied Soft Computing 61 (2017): 264-282.
  * S. Chardon, B. Brangeon, E. Bozonnet, C. Inard (2016), Construction cost and energy performance of single family houses : From integrated design to automated optimization, Automation in Construction, Volume 70, p.1-13.
  * B. Brangeon, E. Bozonnet, C. Inard (2016), Integrated refurbishment of collective housing and optimization process with real products databases, Building Simulation Optimization, pp. 531–538 Newcastle, England.
  * Randal S. Olson, Ryan J. Urbanowicz, Peter C. Andrews, Nicole A. Lavender, La Creis Kidd, and Jason H. Moore (2016). Automating biomedical data science through tree-based pipeline optimization. Applications of Evolutionary Computation, pages 123-137.
  * Randal S. Olson, Nathan Bartley, Ryan J. Urbanowicz, and Jason H. Moore (2016). Evaluation of a Tree-based Pipeline Optimization Tool for Automating Data Science. Proceedings of GECCO 2016, pages 485-492.
  * Van Geit W, Gevaert M, Chindemi G, Rössert C, Courcol J, Muller EB, Schürmann F, Segev I and Markram H (2016). BluePyOpt: Leveraging open source software and cloud infrastructure to optimise model parameters in neuroscience. Front. Neuroinform. 10:17. doi: 10.3389/fninf.2016.00017 https://github.com/BlueBrain/BluePyOpt
  * Lara-Cabrera, R., Cotta, C. and Fernández-Leiva, A.J. (2014). Geometrical vs topological measures for the evolution of aesthetic maps in a rts game, Entertainment Computing,
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
  * DEAP is used in [TPOT](https://github.com/rhiever/tpot), an open source tool that uses genetic programming to optimize machine learning pipelines.
  * DEAP is also used in ROS as an optimization package http://www.ros.org/wiki/deap.
  * DEAP is an optional dependency for [PyXRD](https://github.com/mathijs-dumon/PyXRD), a Python implementation of the matrix algorithm developed for the X-ray diffraction analysis of disordered lamellar structures.
  * DEAP is used in [glyph](https://github.com/Ambrosys/glyph), a library for symbolic regression with applications to [MLC](https://en.wikipedia.org/wiki/Machine_learning_control).

If you want your project listed here, send us a link and a brief description and we'll be glad to add it.
