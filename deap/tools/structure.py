from __future__ import division
import bisect
import copy

try:
    import cPickle as pickle
except ImportError:
    import pickle

from functools import partial
from itertools import chain
from operator import attrgetter, eq


def identity(obj):
    """Returns directly the argument *obj*.
    """
    return obj

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
    
        history = History()
        
        # Decorate the variation operators
        toolbox.decorate("mate", history.decorator)
        toolbox.decorate("mutate", history.decorator)
        
        # Create the population and populate the history
        population = toolbox.population(n=POPSIZE)
        history.update(population)
        
        # Do the evolution, the decorators will take care of updating the
        # history
        # [...]
        
        import matplotlib.pyplot as plt
        import networkx
        
        graph = networkx.DiGraph(history.genealogy_tree)
        graph = graph.reverse()     # Make the grah top-down
        colors = [toolbox.evaluate(history.genealogy_history[i])[0] for i in graph]
        networkx.draw(graph, node_color=colors)
        plt.show()
    
    Using NetworkX in combination with `pygraphviz
    <http://networkx.lanl.gov/pygraphviz/>`_ (dot layout) this amazing
    genealogy tree can be obtained from the OneMax example with a population
    size of 20 and 5 generations, where the color of the nodes indicate there
    fitness, blue is low and red is high.
    
    .. image:: /_images/genealogy.png
       :width: 67%
     
    .. note::
       The genealogy tree might get very big if your population and/or the 
       number of generation is large.
        
    """
    def __init__(self):
        self.genealogy_index = 0
        self.genealogy_history = dict()
        self.genealogy_tree = dict()
        
    def update(self, individuals):
        """Update the history with the new *individuals*. The index present in
        their :attr:`history_index` attribute will be used to locate their
        parents, it is then modified to a unique one to keep track of those
        new individuals. This method should be called on the individuals after
        each variation.
        
        :param individuals: The list of modified individuals that shall be
                            inserted in the history.
        
        If the *individuals* do not have a :attr:`history_index` attribute, 
        the attribute is added and this individual is considered as having no
        parent. This method should be called with the initial population to
        initialize the history.
        
        Modifying the internal :attr:`genealogy_index` of the history or the
        :attr:`history_index` of an individual may lead to unpredictable
        results and corruption of the history.
        """
        try:
            parent_indices = tuple(ind.history_index for ind in individuals)
        except AttributeError:
            parent_indices = tuple()
        
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
        the underlying operation and then calls the :func:`update` function
        with what has been returned by the operator. Finally, it returns the
        individuals with their history parameters modified according to the
        update function.
        """
        def decFunc(func):
            def wrapFunc(*args, **kargs):
                individuals = func(*args, **kargs)
                self.update(individuals)
                return individuals
            return wrapFunc
        return decFunc

    def getGenealogy(self, individual, max_depth=float("inf")):
        """Provide the genealogy tree of an *individual*. The individual must
        have an attribute :attr:`history_index` as defined by
        :func:`~deap.tools.History.update` in order to retrieve its associated
        genealogy tree. The returned graph contains the parents up to
        *max_depth* variations before this individual. If not provided
        the maximum depth is up to the begining of the evolution.

        :param individual: The individual at the root of the genealogy tree.
        :param max_depth: The approximate maximum distance between the root
                          (individual) and the leaves (parents), optional.
        :returns: A dictionary where each key is an individual index and the
                  values are a tuple corresponding to the index of the parents.
        """
        gtree = {}
        visited = set()     # Adds memory to the breadth first search
        def genealogy(index, depth):
            if index not in self.genealogy_tree:
                return             
            depth += 1
            if depth > max_depth:
                return
            parent_indices = self.genealogy_tree[index]
            gtree[index] = parent_indices
            for ind in parent_indices:
                if ind not in visited:
                    genealogy(ind, depth)
                visited.add(ind)
        genealogy(individual.history_index, 0)
        return gtree

class Statistics(list):
    """Object that keeps record of statistics and key-value pair information
    computed during the evolution. When created the statistics object receives
    a *key* argument that is used to get the values on which the function will
    be computed. If not provided the *key* argument defaults to the identity 
    function.

    :param key: A function to access the values on which to compute the
                statistics, optional.

    Values can be retrieved via the *select* method given the appropriate
    key.
    ::
    
        >>> s = Statistics()
        >>> s.register("mean", mean)
        >>> s.register("max", max)
        >>> s.record([1, 2, 3, 4])
        >>> s.record([5, 6, 7, 8])
        >>> s.select("mean")
        [2.5, 6.5]
        >>> s.select("max")
        [4, 8]
        >>> s[-1]["mean"]
        6.5
        >>> mean, max_ = s.select("mean", "max")
        >>> mean[0]
        2.5
        >>> max_[0]
        4
    """
    def __init__(self, key=identity):
        self.key = key
        self.functions = {}
        
        self.header = None
        """Order of the columns to print when using the :meth:`stream` and
        :meth:`__str__` methods. The syntax is a single iterable containing
        string elements. For example, with the previously
        defined statistics class, one can print the generation and the
        fitness average, and maximum with
        ::

            s.header = ("gen", "mean", "max")
        
        If not set the header is built with all fields, in arbritrary order
        on insertion of the first data. The header can be removed by setting
        it to :data:`None`.
        """
        
        self.buffindex = 0

    def __getstate__(self):
        state = {}
        state['functions'] = self.functions
        state['header'] = self.header
        # Most key cannot be pickled in Python 2
        state['key'] = None
        return state

    def __setstate__(self, state):
        self.__init__(state['key'])
        self.functions = state['functions']
        self.header = state['header']

    def register(self, name, function, *args, **kargs):
        """Register a *function* that will be applied on the sequence each
        time :meth:`record` is called.

        :param name: The name of the statistics function as it would appear
                     in the dictionnary of the statistics object.
        :param function: A function that will compute the desired statistics
                         on the data as preprocessed by the key.
        :param argument: One or more argument (and keyword argument) to pass
                         automatically to the registered function when called,
                         optional.
        """        
        self.functions[name] = partial(function, *args, **kargs)

    def select(self, *names):
        """Return a list of values associated to the *names* provided
        in argument in each dictionary of the Statistics object list.
        One list per name is returned in order.
        ::

            >>> s = Statistics()
            >>> s.register("mean", numpy.mean)
            >>> s.register("max", numpy.mean)
            >>> s.record([1,2,3,4,5,6,7])
            >>> s.select("mean")
            [4.0]
            >>> s.select("mean", "max")
            ([4.0], [7.0])
        """
        if len(names) == 1:
            return [entry[names[0]] for entry in self]
        return tuple([entry[name] for entry in self] for name in names)

    def record(self, data=[], **kargs):
        """Apply to the input sequence *data* each registered function 
        and store the results plus the additional information from *kargs*
        in a dictionnary at the end of the list.
        
        :param data: Sequence of objects on which the statistics are computed.
        :param kargs: Additional key-value pairs to record.
        """
        if not self.key:
            raise AttributeError('It is required to set a key after unpickling a %s object.' % self.__class__.__name__)

        if not self.header:
            self.header = kargs.keys() + self.functions.keys()

        values = tuple(self.key(elem) for elem in data)
        
        entry = {}
        for key, func in self.functions.iteritems():
            entry[key] = func(values)
        entry.update(kargs)
        self.append(entry)
    
    def __delitem__(self, key):
        if isinstance(key, slice):
            for i, in range(*key.indices(len(self))):
                self._pop(i)
        else:
            self._pop(key)
        
    def _pop(self, index=0):
        """Retreive and delete element *index*. The header and stream will be
        adjusted to follow the modification.

        :param item: The index of the element to remove, optional. It defaults
                     to the first element.
        
        You can also use the following syntax to delete elements.
        ::
        
            del s[0]
            del s[1::5]
        """
        if index < self.buffindex:
            self.buffindex -= 1
        return super(self.__class__, self).pop(index)

    def setColumns(self, *args):
        """Set which columns will be outputed when calling converting
        the object to a string with `str` or using the stream property.
        The provided arguments must correspond to either the names of
        the registered functions or the keys of keyword arguments 
        provided when calling the record method.
        """
        self.header = args

    @property
    def stream(self):
        """Retrieve the formated unstreamed entries of the database including
        the headers.
        ::

            >>> s = Statistics()
            >>> s.record(gen=0)
            >>> print s.stream
            gen
              0
            >>> s.record(gen=1)
            >>> print s.stream
              1
        """
        startindex, self.buffindex = self.buffindex, len(self)
        return self.__str__(startindex)

    def __str__(self, startindex=0, columns=None):
        if not columns:
            columns = self.header
        columns_len = map(len, columns)

        str_matrix = []
        for line in self[startindex:]:
            str_line = []
            for i, name in enumerate(columns):
                value = line.get(name, "")
                string = "{0:n}" if isinstance(value, float) else "{0}"
                column = string.format(value)
                columns_len[i] = max(columns_len[i], len(column))
                str_line.append(column)
            str_matrix.append(str_line)
 
        template = "\t".join("{%i:<%i}" % (i, l) for i, l in enumerate(columns_len))
        text = (template.format(*line) for line in str_matrix)
        if startindex == 0:
            text = chain([template.format(*columns)], text)
 
        return "\n".join(text)

class MultiStatistics(dict):
    """Dictionary of :class:`Statistics` object allowing to compute
    statistics on multiple keys using a single call to :meth:`record`. It
    takes a set of key-value pairs associating a statistics object to a
    unique name. This name can then be used to retrieve the statistics object.
    ::

        >>> stats1 = Statistics()
        >>> stats2 = Statistics(key=attrgetter("fitness.values"))
        >>> mstats = MultStatistics(genotype=stats1, fitness=stats2)
        >>> mstats.register("mean", numpy.mean, axis=0)
        >>> mstats.register("max", numpy.max)
        >>> mstats.record(pop, gen=0)
        >>> mstats['fitness'].select("mean")
        [5.0]
        >>> mstats['genotype'].select("max")
        [[1,0,0,0]]
        >>> stats1.select("max")
        [[1,0,0,0]]
    """
    def __init__(self, **kargs):
        for name, stats in kargs.items():
            self[name] = stats
        self.buffindex = 0
        self.columns = []

    def setColumns(self, *args):
        """Set which columns will be outputed when calling converting
        the object to a string with `str` or using the stream property.
        The provided arguments must correspond to either the names of
        keys provided during the init or the keys of keyword arguments 
        provided when calling the `record` method.
        """
        self.columns = args
        # self.is_key_column = True
        self.is_key_column = any(self.has_key(arg) for arg in args)
        
    def record(self, data=[], **kargs):
        """Calls :meth:`Statistics.record` with *data* and *kargs* on each
        :class:`Statistics` object.
        
        :param data: Sequence of objects on which the statistics are computed.
        :param kargs: Additional key-value pairs to record.
        """
        if not self.columns:
            args = self.keys()
            self.setColumns(*args)
        
        for stats in self.values():
            stats.record(data, **kargs)

    def register(self, name, function, *args, **kargs):
        """Register a *function* in each :class:`Statistics` object.
        
        :param name: The name of the statistics function as it would appear
                     in the dictionnary of the statistics object.
        :param function: A function that will compute the desired statistics
                         on the data as preprocessed by the key.
        :param argument: One or more argument (and keyword argument) to pass
                         automatically to the registered function when called,
                         optional.
        """
        for stats in self.values():
            stats.register(name, function, *args, **kargs)
    
    @property
    def stream(self):
        """Retrieve the formated unstreamed entries of the database including
        the headers. For the previous multi statistics object the result is
        ::

            >>> print mstats.stream
                    fitness                  genotype              
                   ---------    ------------------------------------
            gen    max  mean    max             mean
              0    6    5.0     [1, 1, 1, 0]    [0.5, 0.33, 0.75, 0]
            >>> mstats.record(pop, gen=1)
            >>> print mstats.stream
              1    8    5.5     [1, 1, 1, 1]    [0.75, 0.5, 1.0, 0.5]
        """
        startindex, self.buffindex = self.buffindex, len(self[self.keys()[0]])
        return self.__str__(startindex)

    def __str__(self, startindex=0):
        matrices = []
        first = next(self.itervalues())
        for column in self.columns:
            if self.has_key(column):
                stats = self[column]
                lines = stats.__str__(startindex).split('\n')
                length = max(len(line.expandtabs()) for line in lines)
                if startindex == 0:
                    lines.insert(0, "-" * length)
                    lines.insert(0, column.center(length))
            else:
                lines = first.__str__(startindex, (column,)).split('\n')
                length = max(len(line.expandtabs()) for line in lines)
                if startindex == 0 and self.is_key_column:
                    lines.insert(0, " " * length) 
                    lines.insert(0, " " * length)
            matrices.append(lines)

        text = ("\t".join(line) for line in zip(*matrices))
        return "\n".join(text)

class HallOfFame(object):
    """The hall of fame contains the best individual that ever lived in the
    population during the evolution. It is lexicographically sorted at all
    time so that the first element of the hall of fame is the individual that
    has the best first fitness value ever seen, according to the weights
    provided to the fitness at creation time.
    
    The insertion is made so that old individuals have priority on new
    individuals. A single copy of each individual is kept at all time, the
    equivalence between two individuals is made by the operator passed to the
    *similar* argument.

    :param maxsize: The maximum number of individual to keep in the hall of
                    fame.
    :param similar: An equivalence operator between two individuals, optional.
                    It defaults to operator :func:`operator.eq`.
    
    The class :class:`HallOfFame` provides an interface similar to a list
    (without being one completely). It is possible to retrieve its length, to
    iterate on it forward and backward and to get an item or a slice from it.
    """
    def __init__(self, maxsize, similar=eq):
        self.maxsize = maxsize
        self.keys = list()
        self.items = list()
        self.similar = similar
    
    def update(self, population):
        """Update the hall of fame with the *population* by replacing the
        worst individuals in it by the best individuals present in
        *population* (if they are better). The size of the hall of fame is
        kept constant.
        
        :param population: A list of individual with a fitness attribute to
                           update the hall of fame with.
        """
        if len(self) == 0 and self.maxsize !=0:
            # Working on an empty hall of fame is problematic for the
            # "for else"
            self.insert(population[0])
        
        for ind in population:
            if ind.fitness > self[-1].fitness or len(self) < self.maxsize:
                for hofer in self:
                    # Loop through the hall of fame to check for any
                    # similar individual
                    if self.similar(ind, hofer):
                        break
                else:
                    # The individual is unique and strictly better than
                    # the worst
                    if len(self) >= self.maxsize:
                        self.remove(-1)
                    self.insert(ind)
    
    def insert(self, item):
        """Insert a new individual in the hall of fame using the
        :func:`~bisect.bisect_right` function. The inserted individual is
        inserted on the right side of an equal individual. Inserting a new 
        individual in the hall of fame also preserve the hall of fame's order.
        This method **does not** check for the size of the hall of fame, in a
        way that inserting a new individual in a full hall of fame will not
        remove the worst individual to maintain a constant size.
        
        :param item: The individual with a fitness attribute to insert in the
                     hall of fame.
        """
        item = copy.deepcopy(item)
        i = bisect.bisect_right(self.keys, item.fitness)
        self.items.insert(len(self) - i, item)
        self.keys.insert(i, item.fitness)
    
    def remove(self, index):
        """Remove the specified *index* from the hall of fame.
        
        :param index: An integer giving which item to remove.
        """
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
        return str(self.items)


class ParetoFront(HallOfFame):
    """The Pareto front hall of fame contains all the non-dominated individuals
    that ever lived in the population. That means that the Pareto front hall of
    fame can contain an infinity of different individuals.
    
    :param similar: A function that tels the Pareto front whether or not two
                    individuals are similar, optional.
    
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
        HallOfFame.__init__(self, None, similar)
    
    def update(self, population):
        """Update the Pareto front hall of fame with the *population* by adding 
        the individuals from the population that are not dominated by the hall
        of fame. If any individual in the hall of fame is dominated it is
        removed.
        
        :param population: A list of individual with a fitness attribute to
                           update the hall of fame with.
        """
        for ind in population:
            is_dominated = False
            has_twin = False
            to_remove = []
            for i, hofer in enumerate(self):    # hofer = hall of famer
                if hofer.fitness.dominates(ind.fitness):
                    is_dominated = True
                    break
                elif ind.fitness.dominates(hofer.fitness):
                    to_remove.append(i)
                elif ind.fitness == hofer.fitness and self.similar(ind, hofer):
                    has_twin = True
                    break
            
            for i in reversed(to_remove):       # Remove the dominated hofer
                self.remove(i)
            if not is_dominated and not has_twin:
                self.insert(ind)

__all__ = ['HallOfFame', 'ParetoFront', 'History', 'Statistics', 'MultiStatistics']

if __name__ == "__main__":

    doctest.run_docstring_examples(Statistics.register, globals())
    doctest.run_docstring_examples(Statistics.record, globals())

    doctest.run_docstring_examples(Checkpoint, globals())
    doctest.run_docstring_examples(Checkpoint.add, globals())


