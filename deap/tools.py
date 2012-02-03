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
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.
"""The :mod:`~deap.tools` module contains the operators for evolutionary
algorithms. They are used to modify, select and move the individuals in their
environment. The set of operators it contains are readily usable in the
:class:`~deap.base.Toolbox`. In addition to the basic operators this module
also contains utility tools to enhance the basic algorithms with
:class:`Statistics`, :class:`HallOfFame`, :class:`Checkpoint`, and
:class:`History`.
"""
from __future__ import division
import bisect
import copy
import inspect
import math
import random

from itertools import chain
from operator import attrgetter, eq
from collections import Sequence
from sys import stdout

try:
    import yaml
    CHECKPOINT_USE_YAML = True
    try:
        from yaml import CDumper as Dumper  # CLoader and CDumper are much
        from yaml import CLoader as Loader  # faster than default ones, but 
    except ImportError:                     # requires LibYAML to be compiled
        from yaml import Dumper
        from yaml import Loader
except ImportError:
    CHECKPOINT_USE_YAML = False
                                            # If yaml ain't present, use 
try:                                        # pickling to dump
    import cPickle as pickle                # cPickle is much faster than 
except ImportError:                         # pickle but only present under
    import pickle                           # CPython

def initRepeat(container, func, n):
    """Call the function *container* with a generator function corresponding
    to the calling *n* times the function *func*.
    
    This helper function can can be used in conjunction with a Toolbox 
    to register a generator of filled containers, as individuals or 
    population.
    
        >>> initRepeat(list, random.random, 2) # doctest: +ELLIPSIS, 
        ...                                    # doctest: +NORMALIZE_WHITESPACE
        [0.4761..., 0.6302...]

    """
    return container(func() for _ in xrange(n))

def initIterate(container, generator):
    """Call the function *container* with an iterable as 
    its only argument. The iterable must be returned by 
    the method or the object *generator*.
    
    
    This helper function can can be used in conjunction with a Toolbox 
    to register a generator of filled containers, as individuals or 
    population.

        >>> from random import sample
        >>> from functools import partial
        >>> gen_idx = partial(sample, range(10), 10)
        >>> initIterate(list, gen_idx)
        [4, 5, 3, 6, 0, 9, 2, 7, 1, 8]

    """
    return container(generator())

def initCycle(container, seq_func, n=1):
    """Call the function *container* with a generator function corresponding
    to the calling *n* times the functions present in *seq_func*.
    
    This helper function can can be used in conjunction with a Toolbox 
    to register a generator of filled containers, as individuals or 
    population.
    
        >>> func_seq = [lambda:1 , lambda:'a', lambda:3]
        >>> initCycle(list, func_seq, 2)
        [1, 'a', 3, 1, 'a', 3]

    """
    return container(func() for _ in xrange(n) for func in seq_func)

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
        help to track the parents and the children through evolution. This
        index will be modified by the :meth:`update` method when a child is
        produced. Modifying the internal :attr:`genealogy_index` of the
        history or the :attr:`history_index` of an individual may lead to
        unpredictable results and corruption of the history.
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


class Checkpoint(object):
    """A checkpoint is a file containing the state of any object that has been
    hooked. While initializing a checkpoint, add the objects that you want to
    be dumped by appending keyword arguments to the initializer or using the 
    :meth:`add`. By default the checkpoint tries to use the YAML format which
    is human readable, if PyYAML is not installed, it uses pickling which is
    not readable. You can force the use of pickling by setting the argument
    *use_yaml* to :data:`False`. 

    In order to use efficiently this module, you must understand properly the
    assignment principles in Python. This module use the *pointers* you passed
    to dump the object, for example the following won't work as desired ::

        >>> my_object = [1, 2, 3]
        >>> cp = Checkpoint(obj=my_object)
        >>> my_object = [3, 5, 6]
        >>> cp.dump("example")
        >>> cp.load("example.ems")
        >>> cp["obj"]
        [1, 2, 3]

    In order to dump the new value of ``my_object`` it is needed to change its
    internal values directly and not touch the *label*, as in the following ::

        >>> my_object = [1, 2, 3]
        >>> cp = Checkpoint(obj=my_object)
        >>> my_object[:] = [3, 5, 6]
        >>> cp.dump("example")
        >>> cp.load("example.ems")
        >>> cp["obj"]
        [3, 5, 6]

    """
    def __init__(self, use_yaml=True, **kargs):
#        self.zipped = zipped
        self._dict = kargs
        if CHECKPOINT_USE_YAML and use_yaml:
            self.use_yaml = True
        else:
            self.use_yaml = False

    def add(self, **kargs):
        """Add objects to the list of objects to be dumped. The object is
        added under the name specified by the argument's name. Keyword
        arguments are mandatory in this function.
        """
        self._dict.update(kargs)

    def remove(self, *args):
        """Remove objects with the specified name from the list of objects to
        be dumped.
        """
        for element in args:
            del self._dict[element]

    def __getitem__(self, value):
        return self._dict[value]

    def dump(self, prefix):
        """Dump the current registered objects in a file named *prefix.ecp*,
        the randomizer state is always added to the file and available under
        the ``"randomizer_state"`` tag.
        """
#        if not self.zipped:
        cp_file = open(prefix + ".ecp", "w")
#        else:
#            file = gzip.open(prefix + ".ems.gz", "w")
        cp = self._dict.copy()
        cp.update({"randomizer_state" : random.getstate()})

        if self.use_yaml:
            cp_file.write(yaml.dump(cp, Dumper=Dumper))
        else:
            pickle.dump(cp, cp_file)

        cp_file.close()

    def load(self, filename):
        """Load a checkpoint file retrieving the dumped objects, it is not
        safe to load a checkpoint file in a checkpoint object that contains
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

def std(seq):
    """Returns the square root of the variance :math:`\sigma^2` of *seq*.
    """
    return var(seq)**0.5
    
def identity(obj):
    """Returns directly the argument *obj*.
    """
    return obj

class Statistics(object):
    """A statistics object that holds the required data for as long as it
    exists. When created the statistics object receives a *key* argument that
    is used to get the required data, if not provided the *key* argument
    defaults to the identity function. A statistics object can be represented
    as multiple 3 dimensional matrix, for each registered function there is
    a matrix.

    Along the first axis (wich length is given by the *n* argument) are
    independent statistics on different collections given this index in the 
    :meth:`update` method. The second is the accumulator of statistics, each 
    time the update function is called the new statistics are added using the 
    registered functions at the end of this axis. The third axis is used when 
    the entered data is an iterable (for example a multiobjective fitness).
    
    Data can be retrieved by accessing the statistic function name followed
    by the indicices of the element we wish to access.
    ::
    
        >>> s = Statistics(n=2)
        >>> s.register("Mean", mean)
        >>> s.update([1, 2, 3, 4], index=0)
        >>> s.update([5, 6, 7, 8], index=1)
        >>> s.Mean[0][-1]
        [2.5]
        >>> s.Mean[1][-1]
        [6.5]
        >>> s.update([10, 20, 30, 40], index=0)
        >>> s.update([50, 60, 70, 80], index=1)
        >>> s.Mean[0][1]
        [25.0]
        >>> s.Mean[1][1]
        [65.0]
    """
    __slots__ = ['key', 'functions', 'dim', 'data']
    def __init__(self, key=identity, n=1):
        self.key = key
        self.data = {}
        self.functions = {}
        self.dim = n

    def __getattr__(self, name):
        if name in self.__getattribute__("data"):
            return self.data[name]
        else:
            return self.__getattribute__(name)

    def __getstate__(self):
        return None, {'key' : self.key, 'functions' : self.functions, 
                      'dim' : self.dim, 'data' : self.data}

    def register(self, name, function):
        """Register a function *function* that will be apply on the sequence
        each time :func:`~deap.tools.Statistics.update` is called.
        The function result will be accessible by using the string given by
        the argument *name* as a function of the statistics object.
        ::

            >>> s = Statistics()
            >>> s.register("Mean", mean)
            >>> s.update([1,2,3,4,5,6,7])
            >>> s.Mean
            [[[4.0]]]
        """
 
        if name in self.__slots__:
            raise ValueError("Statistics.register: The registered name"
                             " can't be 'key', 'functions', 'dim' or 'data'.")
        self.functions[name] = function
        self.data[name] = [[] for _ in xrange(self.dim)]

    def update(self, seq, index=0):
        """Apply to the input sequence *seq* each registered function 
        and store each result in a list specific to the function and 
        the data index *index*.
        ::

            >>> s = Statistics()
            >>> s.register("Mean", mean)
            >>> s.register("Max", max)
            >>> s.update([4,5,6,7,8])
            >>> s.Max
            [[[8]]]
            >>> s.Mean
            [[[6.0]]]
            >>> s.update([1,2,3])
            >>> s.Max
            [[[8], [3]]]
        """

        # Transpose the values
        try:
            # seq is a sequence of number sequences.
            values = zip(*(self.key(elem) for elem in seq))
        except TypeError:
            # seq is a sequence of numbers.
            values = (seq,)

        for key, func in self.functions.iteritems():
            self.data[key][index].append(map(func, values))

class EvolutionLogger(object):
    """
    """

    output = stdout
    """File object indicating where the log is written. By default log is
    written in sys.stdout.
    """
    def __init__(self, col_names=None):
        """
        """
        self.lg_stats_names = ()
        self.lg_stats_values = ()
        self.lg_stat_str = ""
        self.header = ""
        if col_names is not None:
            self.lg_stat_names = tuple(col_names)
            self.lg_stat_str = "".join(tuple(" %12s",) * len(self.lg_stat_names))
            self.header = ("{0:>5s}".format("Gen.") + " {0:>5s}".format("Evals") +
                           (self.lg_stat_str % self.lg_stat_names))
        else:
            self.header = ("{0:>5s}".format("Gen.") + " {0:>5s}".format("Evals"))

    def logHeader(self):
        """Logs the column titles which are "Gen.", "Evals", and the column
        names specified during initialization.
        """
        self.output.write(self.header + "\n")

    def logGeneration(self, nbr_eval, gen):
        """Logs the generation identifier *gen*, which can be a string of any sort, 
        and the number of evaluations *nbr_eval*, which has to be an integer.
        """
        self.output.write("{0:>5s}".format(str(gen)) + 
                          "{0:>5d}".format(nbr_eval) + "\n")

    def logStatistics(self, stats, nbr_eval, gen, index=0):
        """Logs the generation identifier *gen*, the number of evaluations
        *nbr_eval* and the generation statistics *stats* of with the index
        *index*. 
        """
        lg_stat_values = tuple("[%s]" % ", ".join("%.4f" % value for value in
                                                  stats.data[key][index][-1]) 
                               for key in self.lg_stat_names)
        self.output.write("{0:>5s}".format(str(gen)) + " {0:>5d}".format(nbr_eval) +
                     (self.lg_stat_str %  lg_stat_values) + "\n")

class HallOfFame(object):
    """The hall of fame contains the best individual that ever lived in the
    population during the evolution. It is sorted at all time so that the
    first element of the hall of fame is the individual that has the best
    first fitness value ever seen, according to the weights provided to the
    fitness at creation time.
    
    The class :class:`HallOfFame` provides an interface similar to a list
    (without being one completely). It is possible to retrieve its length, to
    iterate on it forward and backward and to get an item or a slice from it.
    """
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.keys = list()
        self.items = list()
    
    def update(self, population):
        """Update the hall of fame with the *population* by replacing the
        worst individuals in it by the best individuals present in
        *population* (if they are better). The size of the hall of fame is
        kept constant.
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
    def __init__(self, similar=eq):
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
    
        >>> ind1 = [A(1), ..., A(i), ..., A(j), ..., A(m)] #doctest: +SKIP
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

        >>> ind1 = [A(1), ..., A(n), ..., A(m)] #doctest: +SKIP
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

        >>> ind1 = [0, 1, 2, 3, 4] #doctest: +SKIP
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

def cxOrdered(ind1, ind2):
    size = min(len(ind1), len(ind2))
    a, b = random.sample(xrange(size), 2)
    if a > b:
        a, b = b, a
    
    holes1, holes2 = [True]*size, [True]*size
    for i in range(size):
        if i < a or i > b:
            holes1[ind2[i]] = False
            holes2[ind1[i]] = False
    
    # We must keep the original values somewhere before scrambling everything
    temp1, temp2 = ind1, ind2
    k1 , k2 = b + 1, b + 1
    for i in range(size):
        if not holes1[temp1[(i + b + 1) % size]]:
            ind1[k1 % size] = temp1[(i + b + 1) % size]
            k1 += 1
        
        if not holes2[temp2[(i + b + 1) % size]]:
            ind2[k2 % size] = temp2[(i + b + 1) % size]
            k2 += 1
    
    # Swap the content between a and b (included)
    for i in range(a, b + 1):
        ind1[i], ind2[i] = ind2[i], ind1[i]
    
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

def cxSimulatedBinary(ind1, ind2, eta):
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
        beta **= 1. / (eta + 1.)
        x1 = ind1[i]
        x2 = ind2[i]
        ind1[i] = 0.5 * (((1 + beta) * x1) + ((1 - beta) * x2))
        ind2[i] = 0.5 * (((1 - beta) * x1) + ((1 + beta) * x2))
    
    return ind1, ind2


def cxSimulatedBinaryBounded(ind1, ind2, eta, low, up):
    """Executes a simulated binary crossover that modify in-place the input
    individuals. The simulated binary crossover expect individuals formed of
    a list of floating point numbers.

    This function use the :func:`~random.random` function from the python base
    :mod:`random` module.

    :note: This implementation is similar to the one implemented in the 
    original NSGA-II C code presented by Deb.
    """
    size = min(len(ind1), len(ind2))
    
    if not isinstance(low, Sequence):
        low = [low] * size
    if not isinstance(up, Sequence):
        up = [up] * size

    for i in xrange(size):
        rand = random.random()
        if rand <= 0.5:
            # This epsilon should probably be changed for 0 since 
            # floating point arithmetic in Python is safer
            if abs(ind1[i] - ind2[i]) > 1e-14:
                x1 = min(ind1[i], ind2[i])
                x2 = max(ind1[i], ind2[i])
                xl = low[i]
                xu = up[i]
                rand = random.random()
                
                beta = 1.0 + (2.0 * (x1 - xl) / (x2 - x1))
                alpha = 2.0 - beta**-(eta + 1)
                if rand <= 1.0 / alpha:
                    beta_q = (rand * alpha)**(1 / (eta + 1))
                else:
                    beta_q = (1.0 / (2.0 - rand * alpha))**(1 / (eta + 1))
                
                c1 = 0.5 * (x1 + x2 - beta_q * (x2 - x1))
                
                beta = 1.0 + (2.0 * (xu - x2) / (x2 - x1))
                alpha = 2.0 - beta**-(eta + 1)
                if rand <= 1.0 / alpha:
                    beta_q = (rand * alpha)**(1 / (eta + 1))
                else:
                    beta_q = (1.0 / (2.0 - rand * alpha))**(1 / (eta + 1))
                c2 = 0.5 * (x1 + x2 + beta_q * (x2 - x1))
                
                c1 = min(max(c1, xl), xu)
                c2 = min(max(c2, xl), xu)
                
                if random.random() <= 0.5:
                    ind1[i] = c2
                    ind2[i] = c1
                else:
                    ind1[i] = c1
                    ind2[i] = c2
    
    return ind1, ind2   


######################################
# Messy Crossovers                   #
######################################

def cxMessyOnePoint(ind1, ind2):
    """Execute a one point crossover that will in most cases change the
    individuals size. This operation apply on an individual composed
    of a list of attributes and act as follow ::

        >>> ind1 = [A(1), ..., A(i), ..., A(m)] #doctest: +SKIP
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

def cxESBlend(ind1, ind2, alpha):
    """Execute a blend crossover on both, the individual and the strategy. The
    individuals must have a :attr:`strategy` attribute. Adjustement of the
    minimal strategy shall be done after the call to this function using a
    decorator, for example ::
    
        def checkStrategy(minstrategy):
            def decMinStrategy(func):
                def wrapMinStrategy(*args, **kargs):
                    children = func(*args, **kargs)
                    for child in children:
                        if child.strategy < minstrategy:
                            child.strategy = minstrategy
                    return children
                return wrapMinStrategy
            return decMinStrategy
        
        toolbox.register("mate", tools.cxEsBlend, alpha=ALPHA)
        toolbox.decorate("mate", checkStrategy(minstrategy=0.01))
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

def mutPolynomialBounded(individual, eta, low, up, indpb):
    """Polynomial mutation as implemented in original NSGA-II algorithm in
    C by Deb.
    """
    size = len(individual)
    if not isinstance(low, Sequence):
        low = [low] * size
    if not isinstance(up, Sequence):
        up = [up] * size
    
    for i in xrange(size):
        if random.random() <= indpb:
            x = individual[i]
            xl = low[i]
            xu = up[i]
            delta_1 = (x - xl) / (xu - xl)
            delta_2 = (xu - x) / (xu - xl)
            rand = random.random()
            mut_pow = 1.0 / (eta + 1.)

            if rand < 0.5:
                xy = 1.0 - delta_1
                val = 2.0 * rand + (1.0 - 2.0 * rand) * xy**(eta + 1)
                delta_q = val**mut_pow - 1.0
            else:
                xy = 1.0 - delta_2
                val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * xy**(eta + 1)
                delta_q = 1.0 - val**mut_pow

            x = x + delta_q * (xu - xl)
            x = min(max(x, xl), xu)
            individual[i] = x
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
            individual[indx] = type(individual[indx])(not individual[indx])
    
    return individual,
    
######################################
# ES Mutations                       #
######################################

def mutESLogNormal(individual, c, indpb):
    """Mutate an evolution strategy according to its :attr:`strategy`
    attribute as described in *Beyer and Schwefel, 2002, Evolution strategies
    - A Comprehensive Introduction*. The individual is first mutated by a
    normal distribution of mean 0 and standard deviation of
    :math:`\\boldsymbol{\sigma}_{t-1}` then the strategy is mutated according
    to an extended log normal rule, 
    :math:`\\boldsymbol{\sigma}_t = \\exp(\\tau_0 \mathcal{N}_0(0, 1)) \\left[
    \\sigma_{t-1, 1}\\exp(\\tau \mathcal{N}_1(0, 1)), \ldots, \\sigma_{t-1, n}
    \\exp(\\tau \mathcal{N}_n(0, 1))\\right]`, with :math:`\\tau_0 =
    \\frac{c}{\\sqrt{2n}}` and :math:`\\tau = \\frac{c}{\\sqrt{2\\sqrt{n}}}`.
    A recommended choice is :math:`c=1` when using a :math:`(10, 100)`
    evolution strategy (Beyer and Schwefel, 2002).
    
    The strategy shall be the same size as the individual. Each index
    (strategy and attribute) is mutated with probability *indpb*. In order to
    limit the strategy, use a decorator as shown in the :func:`cxESBlend`
    function.
    """
    size = len(individual)
    t = c / math.sqrt(2. * math.sqrt(size))
    t0 = c / math.sqrt(2. * size)
    n = random.gauss(0, 1)
    t0_n = t0 * n
    
    for indx in xrange(size):
        if random.random() < indpb:
            individual[indx] += individual.strategy[indx] * random.gauss(0, 1)
            individual.strategy[indx] *= math.exp(t0_n + t * random.gauss(0, 1))
    
    return individual,
    

######################################
# Selections                         #
######################################

def selRandom(individuals, k):
    """Select *k* individuals at random from the input *individuals* with
    replacement. The list returned contains references to the input
    *individuals*.

    This function uses the :func:`~random.choice` function from the
    python base :mod:`random` module.
    """
    return [random.choice(individuals) for i in xrange(k)]


def selBest(individuals, k):
    """Select the *k* best individuals among the input *individuals*. The
    list returned contains references to the input *individuals*.
    """
    return sorted(individuals, key=attrgetter("fitness"), reverse=True)[:k]


def selWorst(individuals, k):
    """Select the *k* worst individuals among the input *individuals*. The
    list returned contains references to the input *individuals*.
    """
    return sorted(individuals, key=attrgetter("fitness"))[:k]


def selTournament(individuals, k, tournsize):
    """Select *k* individuals from the input *individuals* using *k*
    tournaments of *tournSize* individuals. The list returned contains
    references to the input *individuals*.
    
    This function uses the :func:`~random.choice` function from the python base
    :mod:`random` module.
    """
    chosen = []
    for i in xrange(k):
        chosen.append(random.choice(individuals))
        for j in xrange(tournsize - 1):
            aspirant = random.choice(individuals)
            if aspirant.fitness > chosen[i].fitness:
                chosen[i] = aspirant
                
    return chosen

def selRoulette(individuals, k):
    """Select *k* individuals from the input *individuals* using *k*
    spins of a roulette. The selection is made by looking only at the first
    objective of each individual. The list returned contains references to
    the input *individuals*.
    
    This function uses the :func:`~random.random` function from the python base
    :mod:`random` module.
    
    .. warning::
       The roulette selection by definition cannot be used for minimization 
       or when the fitness can be smaller or equal to 0.
    """
    s_inds = sorted(individuals, key=attrgetter("fitness"), reverse=True)
    sum_fits = sum(ind.fitness.values[0] for ind in individuals)
    
    chosen = []
    for i in xrange(k):
        u = random.random() * sum_fits
        sum_ = 0
        for ind in s_inds:
            sum_ += ind.fitness.values[0]
            if sum_ > u:
                chosen.append(ind)
                break
    
    return chosen


def selTournamentDCD(individuals, k):
    """Tournament selection based on dominance (D) and crowding distance (CD).
    The `individuals` sequence length has to have a length which is 
    a multiple of 4. Also, this tournament can only be used in 
    conjunction with an algorithm assigning crowding distance to the
    individual fitnesses. 
    """
    def tourn(ind1, ind2):
        if ind1.fitness.isDominated(ind2.fitness):
            return ind2
        elif ind2.fitness.isDominated(ind1.fitness):
            return ind1

        if ind1.fitness.crowding_dist < ind2.fitness.crowding_dist:
            return ind2
        elif ind1.fitness.crowding_dist > ind2.fitness.crowding_dist:
            return ind1

        if random.random() <= 0.5:
            return ind1
        return ind2

    individuals_1 = random.sample(individuals, len(individuals))
    individuals_2 = random.sample(individuals, len(individuals))

    chosen = []
    for i in xrange(0, k, 4):
        chosen.append(tourn(individuals_1[i],   individuals_1[i+1]))
        chosen.append(tourn(individuals_1[i+2], individuals_1[i+3]))
        chosen.append(tourn(individuals_2[i],   individuals_2[i+1]))
        chosen.append(tourn(individuals_2[i+2], individuals_2[i+3]))

    return chosen

######################################
# Non-Dominated Sorting   (NSGA-II)  #
######################################

def selNSGA2(individuals, k):
    """Apply NSGA-II selection operator on the *individuals*. Usually,
    the size of *individuals* will be larger than *k* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *n* will have no effect other
    than sorting the population according to a non-domination scheme. The list
    returned contains references to the input *individuals*.
    
    For more details on the NSGA-II operator see Deb, Pratab, Agarwal,
    and Meyarivan, "A fast elitist non-dominated sorting genetic algorithm for
    multi-objective optimization: NSGA-II", 2002.
    """
    pareto_fronts = sortFastND(individuals, k)
    for front in pareto_fronts:
        assignCrowdingDist(front)
    
    chosen = list(chain(*pareto_fronts[:-1]))
    k = k - len(chosen)
    if k > 0:
        sorted_front = sorted(pareto_fronts[-1], key=attrgetter("fitness.crowding_dist"), reverse=True)
        chosen.extend(sorted_front[:k])
        
    return chosen
    
def sortFastND(individuals, k, first_front_only=False):
    """Sort the first *k* *individuals* according the the fast non-dominated
    sorting algorithm. 
    """
    N = len(individuals)
    pareto_fronts = []
    
    if k == 0:
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
        N = min(N, k)
        while pareto_sorted < N:
            pareto_fronts.append([])
            for indice_p in pareto_fronts[-2]:
                for indice_d in dominated_inds[indice_p]:
                    dominating_inds[indice_d] -= 1
                    if dominating_inds[indice_d] == 0:
                        pareto_fronts[-1].append(indice_d)
                        pareto_sorted += 1
    
    return [[individuals[index] for index in front] for front in pareto_fronts]


def assignCrowdingDist(individuals):
    """Assign the crowding distance to each individual of the list."""
    if len(individuals) == 0:
        return
    
    distances = [0.0] * len(individuals)
    crowding = [(ind.fitness.values, i) for i, ind in enumerate(individuals)]
    
    number_objectives = len(individuals[0].fitness.values)
    
    for i in xrange(number_objectives):
        crowding.sort(key=lambda element: element[0][i])
        distances[crowding[0][1]] = float("inf")
        distances[crowding[-1][1]] = float("inf")
        for j in xrange(1, len(crowding) - 1):
            distances[crowding[j][1]] += crowding[j + 1][0][i] - \
                                         crowding[j - 1][0][i]

    for i, dist in enumerate(distances):
        individuals[i].fitness.crowding_dist = dist


######################################
# Strength Pareto         (SPEA-II)  #
######################################

def selSPEA2(individuals, k):
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
    
    if len(chosen_indices) < k:     # The archive is too small
        for i in xrange(N):
            distances = [0.0] * N
            for j in xrange(i + 1, N):
                dist = 0.0
                for l in xrange(L):
                    val = individuals[i].fitness.values[l] - \
                          individuals[j].fitness.values[l]
                    dist += val * val
                distances[j] = dist
            kth_dist = _randomizedSelect(distances, 0, N - 1, K)
            density = 1.0 / (kth_dist + 2.0)
            fits[i] += density
            
        next_indices = [(fits[i], i) for i in xrange(N) \
                                                if not i in chosen_indices]
        next_indices.sort()
        #print next_indices
        chosen_indices += [i for _, i in next_indices[:k - len(chosen_indices)]]
                
    elif len(chosen_indices) > k:   # The archive is too large
        N = len(chosen_indices)
        distances = [[0.0] * N for i in xrange(N)]
        sorted_indices = [[0] * N for i in xrange(N)]
        for i in xrange(N):
            for j in xrange(i + 1, N):
                dist = 0.0
                for l in xrange(L):
                    val = individuals[chosen_indices[i]].fitness.values[l] - \
                          individuals[chosen_indices[j]].fitness.values[l]
                    dist += val * val
                distances[i][j] = dist
                distances[j][i] = dist
            distances[i][i] = -1
        
        # Insert sort is faster than quick sort for short arrays
        for i in xrange(N):
            for j in xrange(1, N):
                l = j
                while l > 0 and distances[i][j] < distances[i][sorted_indices[i][l - 1]]:
                    sorted_indices[i][l] = sorted_indices[i][l - 1]
                    l -= 1
                sorted_indices[i][l] = j
        
        size = N
        to_remove = []
        while size > k:
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

def migRing(populations, k, selection, replacement=None, migarray=None):
    """Perform a ring migration between the *populations*. The migration first
    select *k* emigrants from each population using the specified *selection*
    operator and then replace *k* individuals from the associated population
    in the *migarray* by the emigrants. If no *replacement* operator is
    specified, the immigrants will replace the emigrants of the population,
    otherwise, the immigrants will replace the individuals selected by the
    *replacement* operator. The migration array, if provided, shall contain
    each population's index once and only once. If no migration array is
    provided, it defaults to a serial ring migration (1 -- 2 -- ... -- n --
    1). Selection and replacement function are called using the signature
    ``selection(populations[i], k)`` and ``replacement(populations[i], k)``.
    It is important to note that the replacement strategy must select *k*
    **different** individuals. For example, using a traditional tournament for
    replacement strategy will thus give undesirable effects, two individuals
    will most likely try to enter the same slot.
    """
    if migarray is None:
        migarray = range(1, len(populations)) + [0]
    
    immigrants = [[] for i in xrange(len(migarray))]
    emigrants = [[] for i in xrange(len(migarray))]

    for from_deme in xrange(len(migarray)):
        emigrants[from_deme].extend(selection(populations[from_deme], k))
        if replacement is None:
            # If no replacement strategy is selected, replace those who migrate
            immigrants[from_deme] = emigrants[from_deme]
        else:
            # Else select those who will be replaced
            immigrants[from_deme].extend(replacement(populations[from_deme], k))

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


######################################
# Decoration tool                    #
######################################

# This function is a simpler version of the decorator module (version 3.2.0)
# from Michele Simionato available at http://pypi.python.org/pypi/decorator.
# Copyright (c) 2005, Michele Simionato
# All rights reserved.
# Modified by Francois-Michel De Rainville, 2010

def decorate(decorator):
    """Decorate a function preserving its signature. There is two way of
    using this function, first as a decorator passing the decorator to
    use as argument, for example ::

        @decorate(a_decorator)
        def myFunc(arg1, arg2, arg3="default"):
            do_some_work()
            return "some_result"

    Or as a decorator ::

        @decorate
        def myDecorator(func):
            def wrapFunc(*args, **kargs):
                decoration_work()
                return func(*args, **kargs)
            return wrapFunc

        @myDecorator
        def myFunc(arg1, arg2, arg3="default"):
            do_some_work()
            return "some_result"

    Using the :mod:`inspect` module, we can retrieve the signature of the
    decorated function, what is not possible when not using this method. ::

        print inspect.getargspec(myFunc)

    It shall return something like ::

        (["arg1", "arg2", "arg3"], None, None, ("default",))

    This function is a simpler version of the decorator module (version 3.2.0)
    from Michele Simionato available at http://pypi.python.org/pypi/decorator.
    """
    def wrapDecorate(func):
        # From __init__
        assert func.__name__
        if inspect.isfunction(func):
            argspec = inspect.getargspec(func)
            defaults = argspec[-1]
            signature = inspect.formatargspec(formatvalue=lambda val: "",
                                              *argspec)[1:-1]
        elif inspect.isclass(func):
            argspec = inspect.getargspec(func.__init__)
            defaults = argspec[-1]
            signature = inspect.formatargspec(formatvalue=lambda val: "",
                                              *argspec)[1:-1]
        if not signature:
            raise TypeError("You are decorating a non function: %s" % func)

        # Change function name for lambda function that gets the "<lambda>"
        # name, which is incompatible with the def <lambda>(signature) : ...
        # scheme.
        if func.__name__ == "<lambda>":
            func.__name__ = "lambda_func"

        # From create
        src = ("def %(name)s(%(signature)s):\n"
               "    return _call_(%(signature)s)\n") % dict(name=func.__name__,
                                                           signature=signature)

        # From make
        evaldict = dict(_call_=decorator(func))
        reserved_names = set([func.__name__] + \
            [arg.strip(' *') for arg in signature.split(',')])
        for name in evaldict.iterkeys():
            if name in reserved_names:
                raise NameError("%s is overridden in\n%s" % (name, src))
        try:
            # This line does all the dirty work of reassigning the signature
            code = compile(src, "<string>", "single")
            exec code in evaldict
        except:
            raise RuntimeError("Error in generated code:\n%s" % src)
        new_func = evaldict[func.__name__]

        # From update
        new_func.__source__ = src
        new_func.__name__ = func.__name__
        new_func.__doc__ = func.__doc__
        new_func.__dict__ = func.__dict__.copy()
        new_func.func_defaults = defaults
        new_func.__module__ = func.__module__
        return new_func
    return wrapDecorate
    
if __name__ == "__main__":
    import doctest
    
    random.seed(64)
    doctest.run_docstring_examples(initRepeat, globals())
    
    random.seed(64)
    doctest.run_docstring_examples(initIterate, globals())
    doctest.run_docstring_examples(initCycle, globals())
    
    doctest.run_docstring_examples(Statistics.register, globals())
    doctest.run_docstring_examples(Statistics.update, globals())
    
    
