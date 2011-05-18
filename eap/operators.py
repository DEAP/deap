#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
import bisect
import copy
import math
import random
# Needed by Nondominated sorting
from itertools import chain, cycle
from operator import attrgetter
 # used in pareto-front hall of fame for eq
import operator
from collections import defaultdict

try:
    import yaml
    MILESTONE_USE_YAML = True
    try:
        from yaml import CDumper as Dumper  # CLoader and CDumper are much
        from yaml import CLoader as Loader  # faster than default ones, but 
    except ImportError:                     # requires LibYAML to be compiled
        from yaml import Dumper
        from yaml import Loader
except ImportError:
    MILESTONE_USE_YAML = False
                                            # If yaml ain't present, use 
try:                                        # pickling to dump
    import cPickle as pickle                # cPickle is much faster than 
except ImportError:                         # pickle but only present under
    import pickle                           # CPython

class History(object):
    """The :class:`History` class helps to build a genealogy of all the
    individuals produced in the evolution. It contains two attributes,
    the :attr:`genealogy_tree` that is a dictionary of lists indexed by
    individual, the list contain the indices of the parents. The second
    attribute :attr:`genealogy_history` contains every individual indexed
    by their individual number as in the genealogy tree.
    
    The produced genealogy tree is compatible with `NetworkX
    <http://networkx.lanl.gov/index.html>`_, here is how to plot the genealogy
    tree ::
    
        hist = History()
        
        # Do some evolution and fill the history
        
        import matplotlib.pyplot as plt
        import networkx as nx
        
        g = nx.DiGraph(hist.genealogy_tree)
        nx.draw_springs(g)
        plt.show()
    
    .. note::
       The genealogy tree might get very big if your population and/or the 
       number of generation is large.
        
    """
    def __init__(self):
        self.genealogy_index = 0
        self.genealogy_history = dict()
        self.genealogy_tree = dict()
    
    def populate(self, individuals):
        """Populate the history with the initial *individuals*. An attribute
        :attr:`history_index` is added to every individual, this index will 
        help to track the parents and the children through evolution. This index
        will be modified by the :meth:`update` method when a child is produced.
        Modifying the internal :attr:`genealogy_index` of the history or the
        :attr:`history_index` of an individual may lead to unpredictable
        results and corruption of the history.
        """
        for ind in individuals:
            self.genealogy_index += 1
            ind.history_index = self.genealogy_index
            self.genealogy_history[self.genealogy_index] = copy.deepcopy(ind)
            self.genealogy_tree[self.genealogy_index] = list()
        
    def update(self, *individuals):
        """Update the history with the new *individuals*. The index present
        in their :attr:`history_index` attribute will be used to locate their
        parents and modified to a unique one to keep track of those new
        individuals.
        """
        parent_indices = [ind.history_index for ind in individuals]
        
        for ind in individuals:
            self.genealogy_index += 1
            ind.history_index = self.genealogy_index
            self.genealogy_history[self.genealogy_index] = copy.deepcopy(ind)
            self.genealogy_tree[self.genealogy_index] = parent_indices
    
    @property
    def decorator(self):
        """Property that returns an appropriate decorator to enhance the
        operators of the toolbox. The returned decorator assumes that the
        individuals are returned by the operator. First the decorator calls
        the underlying operation and then calls the update function with what
        has been returned by the operator as argument. Finally, it returns 
        the individuals with their history parameters modified according to
        the update function.
        """
        def decFunc(func):
            def wrapFunc(*args, **kargs):
                individuals = func(*args, **kargs)
                self.update(*individuals)
                return individuals
            return wrapFunc
        return decFunc


class Milestone(object):
    """A milestone is a file containing the state of any object that has been
    hooked. While initializing a milestone, add the objects that you want to
    be dumped by appending keyword arguments to the initializer or using the 
    :meth:`add`. By default the milestone tries to use the YAML format which
    is human readable, if PyYAML is not installed, it uses pickling which is
    not readable. You can force the use of pickling by setting the argument
    *yaml* to :data:`False`. 

    In order to use efficiently this module, you must understand properly the
    assignment principles in Python. This module use the *pointers* you passed
    to dump the object, for example the following won't work as desired ::

        >>> my_object = [1, 2, 3]
        >>> ms = Milestone(obj=my_object)
        >>> my_object = [3, 5, 6]
        >>> ms.dump("example")
        >>> ms.load("example.ems")
        >>> ms["obj"]
        [1, 2, 3]

    In order to dump the new value of ``my_object`` it is needed to change its
    internal values directly and not touch the *label*, as in the following ::

        >>> my_object = [1, 2, 3]
        >>> ms = Milestone(obj=my_object)
        >>> my_object[:] = [3, 5, 6]
        >>> ms.dump("example")
        >>> ms.load("example.ems")
        >>> ms["obj"]
        [3, 5, 6]

    """
    def __init__(self, yaml=True, **kargs):
#        self.zipped = zipped
        self._dict = kargs
        if MILESTONE_USE_YAML and yaml:
            self.use_yaml = True
        else:
            self.use_yaml = False

    def add(self, **kargs):
        """Add objects to the list of objects to be dumped. The object is added
        under the name specified by the argument's name. Keyword arguments
        are mandatory in this function."""
        self._dict.update(*kargs)

    def remove(self, *args):
        """Remove objects with the specified name from the list of objects to
        be dumped.
        """
        for element in args:
            del self._dict[element]

    def __getitem__(self, value):
        return self._dict[value]

    def dump(self, prefix):
        """Dump the current registered objects in a file named *prefix.ems*,
        the randomizer state is always added to the file and available under
        the ``"randomizer_state"`` tag.
        """
#        if not self.zipped:
        ms_file = open(prefix + ".ems", "w")
#        else:
#            file = gzip.open(prefix + ".ems.gz", "w")
        ms = self._dict.copy()
        ms.update({"randomizer_state" : random.getstate()})

        if self.use_yaml:
            ms_file.write(yaml.dump(ms, Dumper=Dumper))
        else:
            pickle.dump(ms, ms_file)

        ms_file.close()

    def load(self, filename):
        """Load a milestone file retrieving the dumped objects, it is not safe
        to load a milestone file in a milestone object that contains
        references as all conflicting names will be updated with the new
        values.
        """
        if self.use_yaml:
            self._dict.update(yaml.load(open(filename, "r"), Loader=Loader))
        else:
            self._dict.update(pickle.load(open(filename, "r")))

def mean(seq):
    """Returns the arithmetic mean of the sequence *seq* = 
    :math:`\{x_1,\ldots,x_n\}` as :math:`A = \\frac{1}{n} \sum_{i=1}^n x_i`.
    """
    return sum(seq) / len(seq)

def median(seq):
    """Returns the median of *seq* - the numeric value separating the higher half 
    of a sample from the lower half. If there is an even number of elements in 
    *seq*, it returns the mean of the two middle values.
    """
    sseq = sorted(seq)
    length = len(seq)
    if length % 2 == 1:
        return sseq[int((length - 1) / 2)]
    else:
        return (sseq[int((length - 1) / 2)] + sseq[int(length / 2)]) / 2

def var(seq):
    """Returns the variance :math:`\sigma^2` of *seq* = 
    :math:`\{x_1,\ldots,x_n\}` as
    :math:`\sigma^2 = \\frac{1}{N} \sum_{i=1}^N (x_i - \\mu )^2`,
    where :math:`\\mu` is the arithmetic mean of *seq*.
    """
    return abs(sum(x*x for x in seq) / len(seq) - mean(seq)**2)

def std_dev(seq):
    """Returns the square root of the variance :math:`\sigma^2` of *seq*.
    """
    return var(seq)**0.5

class Stats(object):
    """A statistic object.
    """
    def __init__(self, key=lambda x: x):
        self.key = key
        self.functions = {}
        self.data = defaultdict(list)

    def register(self, name, function):
        self.functions[name] = function
    
    def update(self, seq):
        # Transpose the values
        values = zip(*(self.key(elem) for elem in seq))
        for key, func in self.functions.iteritems():
            self.data[key].append(map(func, values))


class HallOfFame(object):
    """The hall of fame contains the best individual that ever lived in the
    population during the evolution. It is sorted at all time so that the
    first element of the hall of fame is the individual that has the best
    first fitness value ever seen, according to the weights provided to the
    fitness at creation time.
    
    The class :class:`HallOfFame` provides an interface similar to a list
    (without being one completely). It is possible to retrieve its length,
    to iterate on it forward and backward and to get an item or a slice from it.
    """
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.keys = list()
        self.items = list()
    
    def update(self, population):
        """Update the hall of fame with the *population* by replacing the worst
        individuals in the it by the best individuals present in *population*
        (if they are better). The size of the hall of fame is kept constant.
        """
        if len(self) < self.maxsize:
            # Items are sorted with the best fitness first
            self.items = sorted(chain(self, population), 
                                key=attrgetter("fitness"), 
                                reverse=True)[:self.maxsize]
            self.items = [copy.deepcopy(item) for item in self.items]
            # The keys are the fitnesses in reverse order to allow the use
            # of the bisection algorithm 
            self.keys = map(attrgetter("fitness"),
                            reversed(self.items))
        else:
            for ind in population: 
                if ind.fitness > self[-1].fitness:
                    # Delete the worst individual from the front
                    self.remove(-1)
                    # Insert the new individual
                    self.insert(ind)
    
    def insert(self, item):
        """Insert a new individual in the hall of fame using the
        :func:`~bisect.bisect_right` function. The inserted individual is
        inserted on the right side of an equal individual. Inserting a new 
        individual in the hall of fame also preserve the hall of fame's order.
        This method **does not** check for the size of the hall of fame, in a
        way that inserting a new individual in a full hall of fame will not
        remove the worst individual to maintain a constant size.
        """
        item = copy.deepcopy(item)
        i = bisect.bisect_right(self.keys, item.fitness)
        self.items.insert(len(self) - i, item)
        self.keys.insert(i, item.fitness)
    
    def remove(self, index):
        """Remove the specified *index* from the hall of fame."""
        del self.keys[len(self) - (index % len(self) + 1)]
        del self.items[index]
    
    def clear(self):
        """Clear the hall of fame."""
        del self.items[:]
        del self.keys[:]

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]

    def __iter__(self):
        return iter(self.items)

    def __reversed__(self):
        return reversed(self.items)
    
    def __str__(self):
        return str(self.items) + "\n" + str(self.keys)

        
class ParetoFront(HallOfFame):
    """The Pareto front hall of fame contains all the non-dominated individuals
    that ever lived in the population. That means that the Pareto front hall of
    fame can contain an infinity of different individuals.
    
    The size of the front may become very large if it is used for example on
    a continuous function with a continuous domain. In order to limit the number
    of individuals, it is possible to specify a similarity function that will
    return :data:`True` if the genotype of two individuals are similar. In that
    case only one of the two individuals will be added to the hall of fame. By
    default the similarity function is :func:`operator.__eq__`.
    
    Since, the Pareto front hall of fame inherits from the :class:`HallOfFame`, 
    it is sorted lexicographically at every moment.
    """
    def __init__(self, similar=operator.eq):
        self.similar = similar
        HallOfFame.__init__(self, None)
    
    def update(self, population):
        """Update the Pareto front hall of fame with the *population* by adding 
        the individuals from the population that are not dominated by the hall
        of fame. If any individual in the hall of fame is dominated it is
        removed.
        """
        for ind in population:
            is_dominated = False
            has_twin = False
            to_remove = []
            for i, hofer in enumerate(self):    # hofer = hall of famer
                if ind.fitness.isDominated(hofer.fitness):
                    is_dominated = True
                    break
                elif hofer.fitness.isDominated(ind.fitness):
                    to_remove.append(i)
                elif ind.fitness == hofer.fitness and self.similar(ind, hofer):
                    has_twin = True
                    break
            
            for i in reversed(to_remove):       # Remove the dominated hofer
                self.remove(i)
            if not is_dominated and not has_twin:
                self.insert(ind)

######################################
# GA Crossovers                      #
######################################

def cxTwoPoints(ind1, ind2):
    """Execute a two points crossover on the input individuals. The two 
    individuals are modified in place. This operation apply on an individual
    composed of a list of attributes and act as follow ::
    
        >>> ind1 = [A(1), ..., A(i), ..., A(j), ..., A(m)]
        >>> ind2 = [B(1), ..., B(i), ..., B(j), ..., B(k)]
        >>> # Crossover with mating points 1 < i < j <= min(m, k) + 1
        >>> cxTwoPoints(ind1, ind2)
        >>> print ind1, len(ind1)
        [A(1), ..., B(i), ..., B(j-1), A(j), ..., A(m)], m
        >>> print ind2, len(ind2)
        [B(1), ..., A(i), ..., A(j-1), B(j), ..., B(k)], k

    This function use the :func:`~random.randint` function from the python base
    :mod:`random` module.
    """
    size = min(len(ind1), len(ind2))
    cxpoint1 = random.randint(1, size)
    cxpoint2 = random.randint(1, size - 1)
    if cxpoint2 >= cxpoint1:
        cxpoint2 += 1
    else:			# Swap the two cx points
        cxpoint1, cxpoint2 = cxpoint2, cxpoint1
   
    ind1[cxpoint1:cxpoint2], ind2[cxpoint1:cxpoint2] \
        = ind2[cxpoint1:cxpoint2], ind1[cxpoint1:cxpoint2]
        
    return ind1, ind2

def cxOnePoint(ind1, ind2):
    """Execute a one point crossover on the input individuals.
    The two individuals are modified in place. This operation apply on an
    individual composed of a list of attributes
    and act as follow ::

        >>> ind1 = [A(1), ..., A(n), ..., A(m)]
        >>> ind2 = [B(1), ..., B(n), ..., B(k)]
        >>> # Crossover with mating point i, 1 < i <= min(m, k)
        >>> cxOnePoint(ind1, ind2)
        >>> print ind1, len(ind1)
        [A(1), ..., B(i), ..., B(k)], k
        >>> print ind2, len(ind2)
        [B(1), ..., A(i), ..., A(m)], m

    This function use the :func:`~random.randint` function from the
    python base :mod:`random` module.
    """
    size = min(len(ind1), len(ind2))
    cxpoint = random.randint(1, size - 1)
    ind1[cxpoint:], ind2[cxpoint:] = ind2[cxpoint:], ind1[cxpoint:]
    
    return ind1, ind2

def cxUniform(ind1, ind2, indpb):
    """Execute a uniform crossover that modify in place the two individuals.
    The genes are swapped according to the *indpb* probability.
    
    This function use the :func:`~random.random` function from the python base
    :mod:`random` module.
    """
    size = min(len(ind1), len(ind2))    
    for i in xrange(size):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
    
    return ind1, ind2
    
def cxPartialyMatched(ind1, ind2):
    """Execute a partially matched crossover (PMX) on the input individuals.
    The two individuals are modified in place. This crossover expect iterable
    individuals of indices, the result for any other type of individuals is
    unpredictable.

    Moreover, this crossover consists of generating two children by matching
    pairs of values in a certain range of the two parents and swapping the values
    of those indexes. For more details see Goldberg and Lingel, "Alleles,
    loci, and the traveling salesman problem", 1985.

    For example, the following parents will produce the two following children
    when mated with crossover points ``a = 2`` and ``b = 4``. ::

        >>> ind1 = [0, 1, 2, 3, 4]
        >>> ind2 = [1, 2, 3, 4, 0]
        >>> cxPartialyMatched(ind1, ind2)
        >>> print ind1
        [0, 2, 3, 1, 4]
        >>> print ind2
        [2, 3, 1, 4, 0]

    This function use the :func:`~random.randint` function from the python base
    :mod:`random` module.
    """
    size = min(len(ind1), len(ind2))
    p1, p2 = [0]*size, [0]*size

    # Initialize the position of each indices in the individuals
    for i in xrange(size):
        p1[ind1[i]] = i
        p2[ind2[i]] = i
    # Choose crossover points
    cxpoint1 = random.randint(0, size)
    cxpoint2 = random.randint(0, size - 1)
    if cxpoint2 >= cxpoint1:
        cxpoint2 += 1
    else:			# Swap the two cx points
        cxpoint1, cxpoint2 = cxpoint2, cxpoint1
    
    # Apply crossover between cx points
    for i in xrange(cxpoint1, cxpoint2):
        # Keep track of the selected values
        temp1 = ind1[i]
        temp2 = ind2[i]
        # Swap the matched value
        ind1[i], ind1[p1[temp2]] = temp2, temp1
        ind2[i], ind2[p2[temp1]] = temp1, temp2
        # Position bookkeeping
        p1[temp1], p1[temp2] = p1[temp2], p1[temp1]
        p2[temp1], p2[temp2] = p2[temp2], p2[temp1]
    
    return ind1, ind2

def cxUniformPartialyMatched(ind1, ind2, indpb):
    """Execute a uniform partially matched crossover (UPMX) on the input
    individuals. The two individuals are modified in place. This crossover
    expect iterable individuals of indices, the result for any other type of
    individuals is unpredictable.

    Moreover, this crossover consists of generating two children by matching
    pairs of values chosen at random with a probability of *indpb* in the two
    parents and swapping the values of those indexes. For more details see
    Cicirello and Smith, "Modeling GA performance for control parameter
    optimization", 2000.

    For example, the following parents will produce the two following children
    when mated with the chosen points ``[0, 1, 0, 0, 1]``. ::

        >>> ind1 = [0, 1, 2, 3, 4]
        >>> ind2 = [1, 2, 3, 4, 0]
        >>> cxUniformPartialyMatched(ind1, ind2)
        >>> print ind1
        [4, 2, 1, 3, 0]
        >>> print ind2
        [2, 1, 3, 0, 4]

    This function use the :func:`~random.random` and :func:`~random.randint`
    functions from the python base :mod:`random` module.
    """
    size = min(len(ind1), len(ind2))
    p1, p2 = [0]*size, [0]*size

    # Initialize the position of each indices in the individuals
    for i in xrange(size):
        p1[ind1[i]] = i
        p2[ind2[i]] = i
    
    for i in xrange(size):
        if random.random < indpb:
            # Keep track of the selected values
            temp1 = ind1[i]
            temp2 = ind2[i]
            # Swap the matched value
            ind1[i], ind1[p1[temp2]] = temp2, temp1
            ind2[i], ind2[p2[temp1]] = temp1, temp2
            # Position bookkeeping
            p1[temp1], p1[temp2] = p1[temp2], p1[temp1]
            p2[temp1], p2[temp2] = p2[temp2], p2[temp1]
    
    return ind1, ind2

def cxBlend(ind1, ind2, alpha):
    """Executes a blend crossover that modify in-place the input individuals.
    The blend crossover expect individuals formed of a list of floating point
    numbers.
    
    This function use the :func:`~random.random` function from the python base
    :mod:`random` module.
    """
    size = min(len(ind1), len(ind2))
    
    for i in xrange(size):
        gamma = (1. + 2. * alpha) * random.random() - alpha
        x1 = ind1[i]
        x2 = ind2[i]
        ind1[i] = (1. - gamma) * x1 + gamma * x2
        ind2[i] = gamma * x1 + (1. - gamma) * x2
    
    return ind1, ind2

def cxSimulatedBinary(ind1, ind2, nu):
    """Executes a simulated binary crossover that modify in-place the input
    individuals. The simulated binary crossover expect individuals formed of
    a list of floating point numbers.
    
    This function use the :func:`~random.random` function from the python base
    :mod:`random` module.
    """
    size = min(len(ind1), len(ind2))
    
    for i in xrange(size):
        rand = random.random()
        if rand <= 0.5:
            beta = 2. * rand
        else:
            beta = 1. / (2. * (1. - rand))
        beta **= 1. / (nu + 1.)
        x1 = ind1[i]
        x2 = ind2[i]
        ind1[i] = 0.5 * (((1 + beta) * x1) + ((1 - beta) * x2))
        ind2[i] = 0.5 * (((1 - beta) * x1) + ((1 + beta) * x2))
    
    return ind1, ind2
    
######################################
# Messy Crossovers                   #
######################################

def cxMessyOnePoint(ind1, ind2):
    """Execute a one point crossover will mostly change the individuals size.
    This operation apply on an :class:`Individual` composed of a list of
    attributes and act as follow ::

        >>> ind1 = [A(1), ..., A(i), ..., A(m)]
        >>> ind2 = [B(1), ..., B(j), ..., B(n)]
        >>> # Crossover with mating points i, j, 1 <= i <= m, 1 <= j <= n
        >>> cxMessyOnePoint(ind1, ind2)
        >>> print ind1, len(ind1)
        [A(1), ..., A(i - 1), B(j), ..., B(n)], n + j - i
        >>> print ind2, len(ind2)
        [B(1), ..., B(j - 1), A(i), ..., A(m)], m + i - j
    
    This function use the :func:`~random.randint` function from the python base
    :mod:`random` module.        
    """
    cxpoint1 = random.randint(0, len(ind1))
    cxpoint2 = random.randint(0, len(ind2))
    ind1[cxpoint1:], ind2[cxpoint2:] = ind2[cxpoint2:], ind1[cxpoint1:]
    
    return ind1, ind2
    
######################################
# ES Crossovers                      #
######################################

def cxESBlend(ind1, ind2, alpha, minstrategy=None):
    """Execute a blend crossover on both, the individual and the strategy.
    *minstrategy* defaults to None so that if it is not present, the minimal
    strategy will be minus infinity.
    """
    size = min(len(ind1), len(ind2))
    
    for indx in xrange(size):
        # Blend the values
        gamma = (1. + 2. * alpha) * random.random() - alpha
        x1 = ind1[indx]
        x2 = ind2[indx]
        ind1[indx] = (1. - gamma) * x1 + gamma * x2
        ind2[indx] = gamma * x1 + (1. - gamma) * x2
        # Blend the strategies
        gamma = (1. + 2. * alpha) * random.random() - alpha
        s1 = ind1.strategy[indx]
        s2 = ind2.strategy[indx]
        ind1.strategy[indx] = (1. - gamma) * s1 + gamma * s2
        ind2.strategy[indx] = gamma * s1 + (1. - gamma) * s2
        if ind1.strategy[indx] < minstrategy:     # 4 < None = False
            ind1.strategy[indx] = minstrategy
        if ind2.strategy[indx] < minstrategy:
            ind2.strategy[indx] = minstrategy
    
    return ind1, ind2

def cxESTwoPoints(ind1, ind2):
    """Execute a classical two points crossover on both the individual and
    its strategy. The crossover points for the individual and the strategy
    are the same.
    """
    size = min(len(ind1), len(ind2))
    
    pt1 = random.randint(1, size)
    pt2 = random.randint(1, size - 1)
    if pt2 >= pt1:
        pt2 += 1
    else:			# Swap the two cx points
        pt1, pt2 = pt2, pt1
   
    ind1[pt1:pt2], ind2[pt1:pt2] = ind2[pt1:pt2], ind1[pt1:pt2]     
    ind1.strategy[pt1:pt2], ind2.strategy[pt1:pt2] = \
        ind2.strategy[pt1:pt2], ind1.strategy[pt1:pt2]
    
    return ind1, ind2

######################################
# GA Mutations                       #
######################################

def mutGaussian(individual, mu, sigma, indpb):
    """This function applies a gaussian mutation of mean *mu* and standard
    deviation *sigma*  on the input individual and
    returns the mutant. The *individual* is left intact and the mutant is an
    independant copy. This mutation expects an iterable individual composed of
    real valued attributes. The *mutIndxPb* argument is the probability of each
    attribute to be mutated.

    .. note::
       The mutation is not responsible for constraints checking, because
       there is too many possibilities for
       resetting the values. Which way is closer to the representation used
       is up to you.
       
       One easy way to add constraint checking to an operator is to 
       use the function decoration in the toolbox. See the multi-objective
       example (moga_kursawefct.py) for an explicit example.

    This function uses the :func:`~random.random` and :func:`~random.gauss`
    functions from the python base :mod:`random` module.
    """        
    for i in xrange(len(individual)):
        if random.random() < indpb:
            individual[i] += random.gauss(mu, sigma)
    
    return individual,

def mutShuffleIndexes(individual, indpb):
    """Shuffle the attributes of the input individual and return the mutant.
    The *individual* is left intact and the mutant is an independent copy. The
    *individual* is expected to be iterable. The *shuffleIndxPb* argument is the
    probability of each attribute to be moved.

    This function uses the :func:`~random.random` and :func:`~random.randint`
    functions from the python base :mod:`random` module.
    """
    size = len(individual)
    for i in xrange(size):
        if random.random() < indpb:
            swap_indx = random.randint(0, size - 2)
            if swap_indx >= i:
                swap_indx += 1
            individual[i], individual[swap_indx] = \
                individual[swap_indx], individual[i]
    
    return individual,

def mutFlipBit(individual, indpb):
    """Flip the value of the attributes of the input individual and return the
    mutant. The *individual* is left intact and the mutant is an independent
    copy. The *individual* is expected to be iterable and the values of the
    attributes shall stay valid after the ``not`` operator is called on them.
    The *flipIndxPb* argument is the probability of each attribute to be
    flipped.

    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.
    """
    for indx in xrange(len(individual)):
        if random.random() < indpb:
            individual[indx] = not individual[indx]
    
    return individual,
    
######################################
# ES Mutations                       #
######################################

def mutES(individual, indpb, minstrategy=None):
    """Mutate an evolution strategy according to its :attr:`strategy`
    attribute. *minstrategy* defaults to None so that if it is not present,
    the minimal strategy will be minus infinity. The strategy shall be the
    same size as the individual. This is subject to change.
    """
    size = len(individual)
    t = 1. / math.sqrt(2. * math.sqrt(size))
    t0 = 1. / math.sqrt(2. * size)
    n = random.gauss(0, 1)
    t0_n = t0 * n
    
    for indx in xrange(size):
        if random.random() < indpb:
            ni = random.gauss(0, 1)
            individual.strategy[indx] *= math.exp(t0_n + t * ni)
            if individual.strategy[indx] < minstrategy:     # 4 < None = False
                individual.strategy[indx] = minstrategy
            individual[indx] += individual.strategy[indx] * ni
    
    return individual,

######################################
# GP Crossovers                      #
######################################

def cxTreeUniformOnePoint(ind1, ind2):
    """Randomly select in each individual and exchange each subtree with the
    point as root between each individual.
    """    
    try:
        index1 = random.randint(1, ind1.size-1)
        index2 = random.randint(1, ind2.size-1)
    except ValueError:
        return ind1, ind2

    sub1 = ind1.searchSubtreeDF(index1)
    sub2 = ind2.searchSubtreeDF(index2)
    ind1.setSubtreeDF(index1, sub2)
    ind2.setSubtreeDF(index2, sub1)
    
    return ind1, ind2
    
## Strongly Typed GP crossovers
def cxTypedTreeOnePoint(ind1, ind2):
    """Randomly select in each individual and exchange each subtree with the 
    point as root between each individual. Since the node are strongly typed, 
    the operator then make sure the type of second node correspond to the type
    of the first node. If it doesn't, it randomly selects another point in the
    second individual and try again. It tries up to *5* times before
    giving up on the crossover.
    
    .. note::
       This crossover is subject to change for a more effective method 
       of selecting the crossover points.
    """
    # choose the crossover point in each individual
    try:
        index1 = random.randint(1, ind1.size-1)
        index2 = random.randint(1, ind2.size-1)
    except ValueError:
        return ind1, ind2
        
    subtree1 = ind1.searchSubtreeDF(index1)
    subtree2 = ind2.searchSubtreeDF(index2)

    type1 = subtree1.root.ret
    type2 = subtree2.root.ret 

    # try to mate the trees
    # if no crossover point is found after 5 it gives up trying
    # mating individuals.
    tries = 0
    MAX_TRIES = 5
    while not (type1 == type2) and tries < MAX_TRIES:
        index2 = random.randint(1, ind2.size-1)
        subtree2 = ind2.searchSubtreeDF(index2)
        type2 = subtree2.root.ret
        tries += 1
    
    if type1 == type2:
        sub1 = ind1.searchSubtreeDF(index1)
        sub2 = ind2.searchSubtreeDF(index2)
        ind1.setSubtreeDF(index1, sub2)
        ind2.setSubtreeDF(index2, sub1)
    
    return ind1, ind2


def cxTreeKozaOnePoint(ind1, ind2, cxtermpb=0.1):
    """Randomly select in each individual and exchange each subtree with the
    point as root between each individual.

    As defined by Koza, non-terminal primitives are selected for 90% of the
    crossover points, and terminals for 10%. This probability can be adjusted
    with the *cxtermpb* argument.
    """
    size1,size2 = ind1.size, ind2.size

    if size1 == 1 or size2 == 1:
        return ind1,ind2

    termsList1 = [i for i in xrange(1, size1) if ind1.searchSubtreeDF(i).size == 1]
    termsList2 = [i for i in xrange(1, size2) if ind2.searchSubtreeDF(i).size == 1]
    primList1 = [i for i in xrange(1, size1) if i not in termsList1]
    primList2 = [i for i in xrange(1, size2) if i not in termsList2]

    # Crossovers should take primitives 90% of time and terminals 10%
    if random.random() < cxtermpb or len(primList1) == 0:
        # Choose a terminal from the first parent
        index1 = random.choice(termsList1)
        subtree1 = ind1.searchSubtreeDF(index1)
    else:
        # Choose a primitive (non-terminal) from the first parent
        index1 = random.choice(primList1)
        subtree1 = ind1.searchSubtreeDF(index1)

    if random.random() < cxtermpb or len(primList2) == 0:
        # Choose a terminal from the second parent
        index2 = random.choice(termsList2)
        subtree2 = ind2.searchSubtreeDF(index2)
    else:
        # Choose a primitive (non-terminal) from the second parent
        index2 = random.choice(primList2)
        subtree2 = ind2.searchSubtreeDF(index2)

    ind1.setSubtreeDF(index1, subtree2)
    ind2.setSubtreeDF(index2, subtree1)

    return ind1, ind2

## Strongly Typed GP crossovers
def cxTypedTreeKozaOnePoint(ind1, ind2, cxtermpb=0.1):
    """Randomly select in each individual and exchange each subtree with the
    point as root between each individual. Since the node are strongly typed,
    the operator then make sure the type of second node correspond to the type
    of the first node. If it doesn't, it randomly selects another point in the
    second individual and try again. It tries up to *5* times before
    giving up on the crossover.

    As defined by Koza, non-terminal primitives are selected for 90% of the
    crossover points, and terminals for 10%. This probability can be adjusted
    with the *cxtermpb* argument.
    
    .. note::
       This crossover is subject to change for a more effective method
       of selecting the crossover points.
    """
    size1,size2 = ind1.size, ind2.size

    if size1 == 1 or size2 == 1:
        return ind1,ind2

    termsList1 = [i for i in xrange(1, size1) if ind1.searchSubtreeDF(i).size == 1]
    termsList2 = [i for i in xrange(1, size2) if ind2.searchSubtreeDF(i).size == 1]
    primList1 = [i for i in xrange(1, size1) if i not in termsList1]
    primList2 = [i for i in xrange(1, size2) if i not in termsList2]

    # Crossovers should take primitives 90% of time and terminals 10%
    if random.random() < cxtermpb or len(primList1) == 0:
        # Choose a terminal from the first parent
        index1 = random.choice(termsList1)
        subtree1 = ind1.searchSubtreeDF(index1)
    else:
        # Choose a primitive (non-terminal) from the first parent
        index1 = random.choice(primList1)
        subtree1 = ind1.searchSubtreeDF(index1)

    if random.random() < cxtermpb or len(primList2) == 0:
        # Choose a terminal from the second parent
        index2 = random.choice(termsList2)
        subtree2 = ind2.searchSubtreeDF(index2)
    else:
        # Choose a primitive (non-terminal) from the second parent
        index2 = random.choice(primList2)
        subtree2 = ind2.searchSubtreeDF(index2)

    type1 = subtree1.root.ret
    type2 = subtree2.root.ret

    # try to mate the trees
    # if no crossover point is found after MAX_CX_TRY
    # the children are returned without modifications.
    tries = 0
    MAX_CX_TRY = 5
    while not (type1 is type2) and tries != MAX_CX_TRY:
        if random.random() < cxtermpb or len(primList2) == 0:
            index2 = random.choice(termsList2)
            subtree2 = ind2.searchSubtreeDF(index2)
        else:
            index2 = random.choice(primList2)
            subtree2 = ind2.searchSubtreeDF(index2)

        type2 = subtree2.root.ret

        tries += 1


    if type1 is type2:
        ind1.setSubtreeDF(index1, subtree2)
        ind2.setSubtreeDF(index2, subtree1)

    return ind1, ind2

######################################
# GP Mutations                       #
######################################
def mutTreeUniform(individual, expr):
    """Randomly select a point in the Tree, then replace the subtree with
    the point as a root by a randomly generated expression. The expression
    is generated using the method `expr`.
    """
    index = random.randint(0, individual.size-1)
    individual.setSubtreeDF(index, expr(pset=individual.pset))
    
    return individual,

## Strongly Typed GP mutations
def mutTypedTreeUniform(individual, expr):
    """The mutation of strongly typed GP expression is pretty easy. First,
    it finds a subtree. Second, it has to identify the return type of the root
    of  this subtree. Third, it generates a new subtree with a root's type
    corresponding to the original subtree root's type. Finally, the old
    subtree is replaced by the new subtree.
    """
    index = random.randint(0, individual.size-1)
    subtree = individual.searchSubtreeDF(index)  
    individual.setSubtreeDF(index, expr(pset=individual.pset,
                                        type_=subtree.root.ret))
    
    return individual,


def mutTypedTreeNodeReplacement(individual):
    """This operator mutates the individual *individual* that are subjected to
    it. The operator randomly chooses a primitive in the individual
    and replaces it with a randomly selected primitive in *pset* that takes
    the same number of arguments.

    This operator works on strongly typed trees as on normal GP trees.
    """
    if individual.size < 2:
        return individual,

    index = random.randint(1, individual.size-1)
    node = individual.searchSubtreeDF(index)

    if node.size == 1:
        subtree = random.choice(individual.pset.terminals[node.root.ret])()
        individual.setSubtreeDF(index, subtree)

    else:
        # We're going to replace one of the *node* children
        index = random.randint(1, len(node) - 1)
        if node[index].size > 1:
            prim_set = individual.pset.primitives[node[index].root.ret]
            repl_node = random.choice(prim_set)
            while repl_node.args != node[index].root.args:
                repl_node = random.choice(prim_set)
            node[index][0] = repl_node
        else:
            term_set = individual.pset.terminals[node[index].root.ret]
            repl_node = random.choice(term_set)()
            node[index] = repl_node

    return individual,

def mutTypedTreeEphemeral(individual, mode):
    """This operator works on the constants of the tree *ind*.
    In  *mode* ``"one"``, it will change the value of **one**
    of the individual ephemeral constants by calling its generator function.
    In  *mode* ``"all"``, it will change the value of **all**
    the ephemeral constants.

    This operator works on strongly typed trees as on normal GP trees.
    """
    if mode not in ["one", "all"]:
        raise ValueError("Mode must be one of \"one\" or \"all\"")
    ephemerals = []
    for i in xrange(1, individual.size):
        subtree = individual.searchSubtreeDF(i)
        if hasattr(subtree.root.obj, 'regen'):
            ephemerals.append(i)

    if len(ephemerals) > 0:
        if mode == "one":
            ephemerals = [random.choice(ephemerals)]
        elif mode == "all":
            pass

        for i in ephemerals:
            individual.searchSubtreeDF(i).regen()
            
    return individual,

def mutTreeShrink(individual):
    """This operator shrinks the individual *individual* that are subjected to
    it. The operator randomly chooses a branch in the individual and replaces
    it with one of the branch's arguments (also randomly chosen).

    This operator is not usable with STGP.
    """
    if individual.size < 3 or individual.height <= 2:
        return individual,       # We don't want to "shrink" the root

    index = random.randint(1, individual.size-2)
    
    # Shrinking a terminal is useless
    while individual.searchSubtreeDF(index).size == 1:
        index = random.randint(1, individual.size-2)

    deleted_node = individual.searchSubtreeDF(index)
    repl_subtree_index = random.randint(1, len(deleted_node)-1)

    individual.setSubtreeDF(index, deleted_node[repl_subtree_index])

    return individual,

def mutTypedTreeInsert(individual):
    """This operator mutate the GP tree of the *individual* passed and the
    primitive set *expr*, by inserting a new branch at a random position in a
    tree, using the original subtree at this position as one argument,
    and if necessary randomly selecting terminal primitives
    to complete the arguments of the inserted node.
    Note that the original subtree will become one of the children of the new
    primitive inserted, but not perforce the first (its position is
    randomly selected if the new primitive has more than one child)

    This operator works on strongly typed trees as on normal GP trees.
    """
    pset = individual.pset
    index = random.randint(0, individual.size-1)
    node = individual.searchSubtreeDF(index)
    if node.size > 1:     # We do not need to deepcopy the leafs
        node = copy.deepcopy(node)
    
    new_primitive = random.choice(pset.primitives[node.root.ret])

    inserted_list = [new_primitive]
    for i in xrange(0, new_primitive.arity):
        # Why don't we use expr to create the other subtrees?
        # Bloat control?
        new_child = random.choice(pset.terminals[new_primitive.args[i]])
        inserted_list.append(new_child())

    inserted_list[random.randint(1, new_primitive.arity)] = node

    individual.setSubtreeDF(index, inserted_list)
    return individual,


# In order to use different mutations, wheter build your own algorithms
# or define your own mutate function that calls explicitely the needed
# methods
# def mutTreeRandomMethod(individual, expr):
#     """This operator performs a mutation over the individual *ind*.
#     The mutation operator is randomly chosen between the insertion,
#     the shrink, the node replacement, the subtree replacement (mutTreeUniform)
#     and the ephemeral constants change.
#     """
#     method = random.choice([mutTreeUniform, mutTypedTreeInsert,
#                             mutTreeShrink, mutTypedTreeNodeReplacement,
#                             mutTypedTreeEphemeral])
#     # Partial? 
#     return functools.partial(method, individual=individual, expr=expr)()

######################################
# Selections                         #
######################################

def selRandom(individuals, n):
    """Select *n* individuals at random from the input *individuals*. The
    list returned contains references to the input *individuals*.

    This function uses the :func:`~random.choice` function from the
    python base :mod:`random` module.
    """
    return [random.choice(individuals) for i in xrange(n)]


def selBest(individuals, n):
    """Select the *n* best individuals among the input *individuals*. The
    list returned contains references to the input *individuals*.
    """
    return sorted(individuals, key=attrgetter("fitness"), reverse=True)[:n]


def selWorst(individuals, n):
    """Select the *n* worst individuals among the input *individuals*. The
    list returned contains references to the input *individuals*.
    """
    return sorted(individuals, key=attrgetter("fitness"))[:n]


def selTournament(individuals, n, tournsize):
    """Select *n* individuals from the input *individuals* using *n*
    tournaments of *tournSize* individuals. The list returned contains
    references to the input *individuals*.
    
    This function uses the :func:`~random.choice` function from the python base
    :mod:`random` module.
    """
    chosen = []
    for i in xrange(n):
        chosen.append(random.choice(individuals))
        for j in xrange(tournsize - 1):
            aspirant = random.choice(individuals)
            if aspirant.fitness > chosen[i].fitness:
                chosen[i] = aspirant
                
    return chosen

def selRoulette(individuals, n):
    """Select *n* individuals from the input *individuals* using *n*
    spins of a roulette. The selection is made by looking only at the first
    objective of each individual. The list returned contains references to
    the input *individuals*.
    
    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.
    """
    s_inds = sorted(individuals, key=attrgetter("fitness"), reverse=True)
    sum_fits = sum(map(lambda ind: ind.fitness.values[0], individuals))
    
    chosen = []
    for i in xrange(n):
        u = random.random() * sum_fits
        sum_ = 0
        for ind in s_inds:
            sum_ += ind.fitness.values[0]
            if sum_ > u:
                chosen.append(ind)
                break
    
    return chosen

######################################
# Non-Dominated Sorting   (NSGA-II)  #
######################################

def selNSGA2(individuals, n):
    """Apply NSGA-II selection operator on the *individuals*. Usually,
    the size of *individuals* will be larger than *n* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *n* will have no effect other
    than sorting the population according to a non-domination scheme. The list
    returned contains references to the input *individuals*.
    
    For more details on the NSGA-II operator see Deb, Pratab, Agarwal,
    and Meyarivan, "A fast elitist non-dominated sorting genetic algorithm for
    multi-objective optimization: NSGA-II", 2002.
    """
    pareto_fronts = sortFastND(individuals, n)
    chosen = list(chain(*pareto_fronts[:-1]))
    n = n - len(chosen)
    if n > 0:
        chosen.extend(sortCrowdingDist(pareto_fronts[-1], n))
    return chosen
    

def sortFastND(individuals, n, first_front_only=False):
    """Sort the first *n* *individuals* according the the fast non-dominated
    sorting algorithm. 
    """
    N = len(individuals)
    pareto_fronts = []
    
    if n == 0:
        return pareto_fronts
    
    pareto_fronts.append([])
    pareto_sorted = 0
    dominating_inds = [0] * N
    dominated_inds = [list() for i in xrange(N)]
    
    # Rank first Pareto front
    for i in xrange(N):
        for j in xrange(i+1, N):
            if individuals[j].fitness.isDominated(individuals[i].fitness):
                dominating_inds[j] += 1
                dominated_inds[i].append(j)
            elif individuals[i].fitness.isDominated(individuals[j].fitness):
                dominating_inds[i] += 1
                dominated_inds[j].append(i)
        if dominating_inds[i] == 0:
            pareto_fronts[-1].append(i)
            pareto_sorted += 1
    
    if not first_front_only:
    # Rank the next front until all individuals are sorted or the given
    # number of individual are sorted
        N = min(N, n)
        while pareto_sorted < N:
            pareto_fronts.append([])
            for indice_p in pareto_fronts[-2]:
                for indice_d in dominated_inds[indice_p]:
                    dominating_inds[indice_d] -= 1
                    if dominating_inds[indice_d] == 0:
                        pareto_fronts[-1].append(indice_d)
                        pareto_sorted += 1
    
    return [[individuals[index] for index in front] for front in pareto_fronts]


def sortCrowdingDist(individuals, n):
    """Sort the individuals according to the crowding distance."""
    if len(individuals) == 0:
        return []
    
    distances = [0.0] * len(individuals)
    crowding = [(ind, i) for i, ind in enumerate(individuals)]
    
    number_objectives = len(individuals[0].fitness.values)
    inf = float("inf")      # It is four times faster to compare with a local
                            # variable than create the float("inf") each time
    for i in xrange(number_objectives):
        crowding.sort(key=lambda element: element[0].fitness.values[i])
        distances[crowding[0][1]] = float("inf")
        distances[crowding[-1][1]] = float("inf")
        for j in xrange(1, len(crowding) - 1):
            if distances[crowding[j][1]] < inf:
                distances[crowding[j][1]] += \
                    crowding[j + 1][0].fitness.values[i] - \
                    crowding[j - 1][0].fitness.values[i]
    sorted_dist = sorted([(dist, i) for i, dist in enumerate(distances)],
                         key=lambda value: value[0], reverse=True)
    return (individuals[index] for dist, index in sorted_dist[:n])


######################################
# Strength Pareto         (SPEA-II)  #
######################################

def selSPEA2(individuals, n):
    """Apply SPEA-II selection operator on the *individuals*. Usually,
    the size of *individuals* will be larger than *n* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *n* will have no effect other
    than sorting the population according to a strength Pareto scheme. The list
    returned contains references to the input *individuals*.
    
    For more details on the SPEA-II operator see Zitzler, Laumanns and Thiele,
    "SPEA 2: Improving the strength Pareto evolutionary algorithm", 2001.
    """
    N = len(individuals)
    L = len(individuals[0].fitness.values)
    K = math.sqrt(N)
    strength_fits = [0] * N
    fits = [0] * N
    dominating_inds = [list() for i in xrange(N)]
    
    for i in xrange(N):
        for j in xrange(i + 1, N):
            if individuals[i].fitness.isDominated(individuals[j].fitness):
                strength_fits[j] += 1
                dominating_inds[i].append(j)
            elif individuals[j].fitness.isDominated(individuals[i].fitness):
                strength_fits[i] += 1
                dominating_inds[j].append(i)
    
    for i in xrange(N):
        for j in dominating_inds[i]:
            fits[i] += strength_fits[j]
    
    # Choose all non-dominated individuals
    chosen_indices = [i for i in xrange(N) if fits[i] < 1]
    
    if len(chosen_indices) < n:     # The archive is too small
        for i in xrange(N):
            distances = [0.0] * N
            for j in xrange(i + 1, N):
                dist = 0.0
                for k in xrange(L):
                    val = individuals[i].fitness.values[k] - \
                          individuals[j].fitness.values[k]
                    dist += val * val
                distances[j] = dist
            kth_dist = _randomizedSelect(distances, 0, N - 1, K)
            density = 1.0 / (kth_dist + 2.0)
            fits[i] += density
            
        next_indices = [(fits[i], i) for i in xrange(N) \
                                                if not i in chosen_indices]
        next_indices.sort()
        #print next_indices
        chosen_indices += [i for fit, i in next_indices[:n - len(chosen_indices)]]
                
    elif len(chosen_indices) > n:   # The archive is too large
        N = len(chosen_indices)
        distances = [[0.0] * N for i in xrange(N)]
        sorted_indices = [[0] * N for i in xrange(N)]
        for i in xrange(N):
            for j in xrange(i + 1, N):
                dist = 0.0
                for k in xrange(L):
                    val = individuals[chosen_indices[i]].fitness.values[k] - \
                          individuals[chosen_indices[j]].fitness.values[k]
                    dist += val * val
                distances[i][j] = dist
                distances[j][i] = dist
            distances[i][i] = -1
        
        # Insert sort is faster than quick sort for short arrays
        for i in xrange(N):
            for j in xrange(1, N):
                k = j
                while k > 0 and distances[i][j] < distances[i][sorted_indices[i][k - 1]]:
                    sorted_indices[i][k] = sorted_indices[i][k - 1]
                    k -= 1
                sorted_indices[i][k] = j
        
        size = N
        to_remove = []
        while size > n:
            # Search for minimal distance
            min_pos = 0
            for i in xrange(1, N):
                for j in xrange(1, size):
                    dist_i_sorted_j = distances[i][sorted_indices[i][j]]
                    dist_min_sorted_j = distances[min_pos][sorted_indices[min_pos][j]]
                    
                    if dist_i_sorted_j < dist_min_sorted_j:
                        min_pos = i
                        break
                    elif dist_i_sorted_j > dist_min_sorted_j:
                        break
            
            # Remove minimal distance from sorted_indices
            for i in xrange(N):
                distances[i][min_pos] = float("inf")
                distances[min_pos][i] = float("inf")
                
                for j in xrange(1, size - 1):
                    if sorted_indices[i][j] == min_pos:
                        sorted_indices[i][j] = sorted_indices[i][j + 1]
                        sorted_indices[i][j + 1] = min_pos
            
            # Remove corresponding individual from chosen_indices
            to_remove.append(min_pos)
            size -= 1
        
        for index in reversed(sorted(to_remove)):
            del chosen_indices[index]
    
    return [individuals[i] for i in chosen_indices]
    
def _randomizedSelect(array, begin, end, i):
    """Allows to select the ith smallest element from array without sorting it.
    Runtime is expected to be O(n).
    """
    if begin == end:
        return array[begin]
    q = _randomizedPartition(array, begin, end)
    k = q - begin + 1
    if i < k:
        return _randomizedSelect(array, begin, q, i)
    else:
        return _randomizedSelect(array, q + 1, end, i - k)

def _randomizedPartition(array, begin, end):
    i = random.randint(begin, end)
    array[begin], array[i] = array[i], array[begin]
    return _partition(array, begin, end)
    
def _partition(array, begin, end):
    x = array[begin]
    i = begin - 1
    j = end + 1
    while True:
        j -= 1
        while array[j] > x:
            j -= 1
        i += 1
        while array[i] < x:
            i += 1
        if i < j:
            array[i], array[j] = array[j], array[i]
        else:
            return j

######################################
# Replacement Strategies (ES)        #
######################################



######################################
# Migrations                         #
######################################

def migRing(populations, n, selection, replacement=None, migarray=None,
            sel_kargs=None, repl_kargs=None):
    """Perform a ring migration between the *populations*. The migration first
    select *n* emigrants from each population using the specified *selection*
    operator and then replace *n* individuals from the associated population in
    the *migarray* by the emigrants. If no *replacement*
    operator is specified, the immigrants will replace the emigrants of the
    population, otherwise, the immigrants will replace the individuals selected
    by the *replacement* operator. The migration array, if provided, shall
    contain each population's index once and only once. If no migration array
    is provided, it defaults to a serial ring migration (1 -- 2 -- ... -- n
    -- 1). You may pass keyword arguments to the two selection operators by
    giving a dictionary to *sel_kargs* and *repl_kargs*.
    """
    if migarray is None:
        migarray = range(1, len(populations)) + [0]
    
    immigrants = [[] for i in xrange(len(migarray))]
    emigrants = [[] for i in xrange(len(migarray))]
    if sel_kargs is None:
        sel_kargs = {}
    if repl_kargs is None:
        repl_kargs = {}

    for from_deme in xrange(len(migarray)):
        emigrants[from_deme].extend(selection(populations[from_deme], n=n,
                                     **sel_kargs))
        if replacement is None:
            # If no replacement strategy is selected, replace those who migrate
            immigrants[from_deme] = emigrants[from_deme]
        else:
            # Else select those who will be replaced
            immigrants[from_deme].extend(replacement(populations[from_deme],
                                          n=n, **repl_kargs))

    mig_buf = emigrants[0]
    for from_deme, to_deme in enumerate(migarray[1:]):
        from_deme += 1  # Enumerate starts at 0

        for i, immigrant in enumerate(immigrants[to_deme]):
            indx = populations[to_deme].index(immigrant)
            populations[to_deme][indx] = emigrants[from_deme][i]

    to_deme = migarray[0]
    for i, immigrant in enumerate(immigrants[to_deme]):
        indx = populations[to_deme].index(immigrant)
        populations[to_deme][indx] = mig_buf[i]