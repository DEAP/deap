简体中文 | [English](./README.md)

# DEAP

[![Build status](https://travis-ci.org/DEAP/deap.svg?branch=master)](https://travis-ci.org/DEAP/deap) [![Download](https://img.shields.io/pypi/dm/deap.svg)](https://pypi.python.org/pypi/deap) [![Join the chat at https://gitter.im/DEAP/deap](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/DEAP/deap?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![Build Status](https://dev.azure.com/fderainville/DEAP/_apis/build/status/DEAP.deap?branchName=master)](https://dev.azure.com/fderainville/DEAP/_build/latest?definitionId=1&branchName=master) [![Documentation Status](https://readthedocs.org/projects/deap/badge/?version=master)](https://deap.readthedocs.io/en/master/?badge=master)

DEAP 是一款新型的进化计算框架，用于快速原型设计和测试想法，旨在能够使得算法明确、数据结构透明。它能够与并行机制（例如多进程和 [SCOOP](https://github.com/soravux/scoop)）完美协作。

DEAP 包含以下特性:

* 使用任何你能够想象到的数据形式使用遗传算法

   * 列表、数组、集合、字典、树、NumPy 数组等

* 使用前缀树进行遗传编程

   * 松散类型，强类型
   * 自动定义函数

* 进化策略（包括 CMA-ES）
* 多目标优化（NSGA-II、NSGA-III、SPEA2、MO-CMA-ES）
* 多个种群的共同进化（合作和竞争）
* 评估的并行化（以及更多其他的情况）
* 最佳个体的名人堂，记录在种群中生活过的最佳个体
* 定期快照系统的检查点
* 基准模块，包含最常见的测试函数
* 进化的谱系（与 [NetworkX](https://github.com/networkx/networkx) 兼容）
* 替代算法的示例：粒子群优化、差分进化、分布估计算法

## 下载

在 Python 社区接受 [PEP 438](http://www.python.org/dev/peps/pep-0438/) 之后，我们已经将 DEAP 的源代码发布到了 PyPI。

你可以在这里找到最新的发布版本：: https://pypi.python.org/pypi/deap/.

## 文档

请参阅 [DEAP User's Guide](http://deap.readthedocs.org/) 用户指南以获取 DEAP 的文档。

为了获取最新的文档，请切换到 `doc` 子文件夹并输入 `make html`, 文档在 [Sphinx](http://sphinx.pocoo.org) 目录下。之后你会用到这个文档。

### Notebooks

你还可以查看我们的新的[notebook examples](https://github.com/DEAP/notebooks)示例。使用 Jupyter 笔记本，你将能够进行导航，并且可以逐个执行代码块以了解每一行的作用。你也可以通过页面底部的链接在线查看 notebook，或者下载 notebook 到本地运行。

```bash
jupyter notebook
```

## 下载

我们提倡使用 easy_install 或者 pip 下载 DEAP 到你自己的系统里。对于其他的安装程序，比如 apt-get, yum 等，通常提供的不是最新的版本。

```bash
pip install deap
```

可以使用下面的命令获取最新版本

```bash
pip install git+https://github.com/DEAP/deap@master
```

如果你想通过源代码进行构建，下载或者克隆仓库，可以使用

```bash
python setup.py install
```

## 构建状态

EAP 的构建状态可以在 Travis-CI 上查看，网址为 https://travis-ci.org/DEAP/deap.

## 依赖

DEAP 的最基本功能依赖于 Python 2.6。为了能够将工具箱与多进程模块结合使用，需要 Python 2.7，因为它支持对部分函数进行序列化（pickle）。CMA-ES 需要使用到 Numpy，我们推荐使用 matplotlib 进行可视化，因为它能够与 DEAP 的 API 完全兼容。

自从 0.8 版本以来，DEAP 可以开箱即用地与 Python 3 兼容。安装过程中会自动使用 2to3 将源代码转换为 Python 3，但这需要 `setuptools<=58`。我们建议使用 `pip install setuptools==57.5.0` 来解决此问题。

## 示例

以下代码简单概述了如何使用 DEAP 实现 Onemax 问题优化的遗传算法。更多示例可以在 [这里](http://deap.readthedocs.org/en/master/examples/index.html) 找到。

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

## 如何引用 DEAP

在科学论文中，包括使用 DEAP 生成的结果，我们鼓励作者引用以下论文。

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

## 研究过程中使用 DEAP 的论文

* François-Michel De Rainville, Félix-Antoine Fortin, Marc-André Gardner, Marc Parizeau and Christian Gagné, "DEAP -- Enabling Nimbler Evolutions", SIGEVOlution, vol. 6, no 2, pp. 17-26, February 2014. [Paper](http://goo.gl/tOrXTp)
* Félix-Antoine Fortin, François-Michel De Rainville, Marc-André Gardner, Marc Parizeau and Christian Gagné, "DEAP: Evolutionary Algorithms Made Easy", Journal of Machine Learning Research, vol. 13, pp. 2171-2175, jul 2012. [Paper](http://goo.gl/amJ3x)
* François-Michel De Rainville, Félix-Antoine Fortin, Marc-André Gardner, Marc Parizeau and Christian Gagné, "DEAP: A Python Framework for Evolutionary Algorithms", in !EvoSoft Workshop, Companion proc. of the Genetic and Evolutionary Computation Conference (GECCO 2012), July 07-11 2012. [Paper](http://goo.gl/pXXug)

## 使用 DEAP 的项目

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
* DEAP is used in [Sklearn-genetic-opt](https://github.com/rodrigo-arenas/Sklearn-genetic-opt), an open source tool that uses evolutionary programming to fine tune machine learning hyperparameters.

如果你希望你的项目在这里列出，请发送链接和简要描述，我们将很高兴添加。
