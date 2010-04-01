#
#    Copyright 2010, Francois-Michel De Rainville and Felix-Antoine Fortin.
#    
#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

'''The :mod:`base` module of EAP contains the basic structures to be used in an
evolutionary algorithm. The :class:`Population` structure is intended to
contain a set of abstract representations of candidate solutions to the
optimisation problem. Each of those potential solutions are called
:class:`Individual`. The individuals are usualy composed of a set of attributes
(widely called genes) and a :class:`Fitness` that describes how good a solution
is to the problem.

Each structure of the :mod:`base` module may be built directly on its own
or concatenated with other structure. For example, a population may contain
individuals or other populations. In the former, the population would behave
as a monodemic evolutionnary algorithm and in the later, as a multidemic
evolutionary algorithm.

The derived structures in the :mod:`base` module are only intended to provide
basic tools to build simple evolutionary algorithm and much more complex
structures may be developed, in wich case we are strongly interested to get
feebacks about implementation.
'''

import array
import copy
import operator
import random

from collections import deque
from itertools import izip, repeat, count, chain, imap

class List(list):
    def __init__(self, size=0, content=None):
        if content is not None:
            if callable(content):
                self.extend(content() for i in xrange(size))
            else:
                self.extend(content)

class Array(array.array):
    def __new__(cls, typecode, **kargs):
        return super(Array, cls).__new__(cls, typecode)

    def __init__(self, size=0, content=None):
        if content is not None:
            if callable(content):
                self.extend(content() for i in xrange(size))
            else:
                self.extend(content)

    def __deepcopy__(self, memo):
        cls = self.__class__
        copy_ = cls.__new__(cls, typecode=self.typecode)
        memo[id(self)] = copy_
        copy_.__dict__.update(copy.deepcopy(self.__dict__, memo))
        copy_.extend(self)
        return copy_

class Indices(Array):
    def __new__(cls, **kargs):
        return super(Array, cls).__new__(cls, "i")
    
    def __init__(self, size=0):
        self.extend(i for i in xrange(size))
        random.shuffle(self)
        
        
class Tree(list):
    """ Basic N-ary tree class"""
    @classmethod
    def create_node(cls, obj):
        try:
            Node = type('Node', (obj.__class__,), {})
        except TypeError:
            if callable(obj):
                Node = type('Node', (object,), {"__call__":staticmethod(obj)})

        Node.count_nodes = staticmethod(lambda: 1)
        Node.height = staticmethod(lambda: 0)

        try:
            new_node = Node(obj)
        except TypeError:
            new_node = Node.__new__(Node)
            new_node.__dict__.update(obj.__dict__)
            
        return new_node

    @classmethod
    def rectify_subtree(cls, subtree):
        if isinstance(subtree, Tree):
            if len(subtree) > 1:
                return subtree
            else:
                return subtree[0]
        else:
            return subtree

    def __init__(self, content=None):
        list.__init__(self)
        if hasattr(content, "__call__"):
            content = content()
        for elem in content:
            if isinstance(elem, list):
                self.append(Tree(elem))
            else:
                self.append(Tree.create_node(elem))

    def count_nodes(self):
        """ This method returns the number of nodes in the tree."""
        return sum(elem.count_nodes() for elem in self)

    def height(self):
        """ This method returns the height of the tree."""
        return max(elem.height() for elem in self)+1

    def search_subtree_dfs(self, index):
        """ This method searches the subtree with the
            corresponding index based on a depth first
            search.
        """
        if index == 0:
            return self
        total = 0
        for child in self:
            if total == index:
                return child
            nbr_child = child.count_nodes()
            if nbr_child + total > index:
                return child.search_subtree_dfs(index-total)
            total += nbr_child

    def set_subtree_dfs(self, index, subtree):
        """ This method replaced the tree with
            the corresponding index by subtree based
            on a depth-first search.
        """
        if index == 0:
            self[:] = subtree
            return
        total = 0
        for i, child in enumerate(self):
            if total == index:
                self[i] = Tree.rectify_subtree(subtree)
                return
            nbr_child = child.count_nodes()
            if nbr_child + total > index:
                child.set_subtree_dfs(index-total, subtree)
                return
            total += nbr_child

    def search_subtree_bfs(self, index):
        """ This method searches the subtree with the
            corresponding index based on a breadth-first
            search.
        """
        if index == 0:
            return self
        queue = deque(self[1:])
        total = 0
        while total != index:
            total += 1
            subtree = queue.popleft()
            if isinstance(subtree, Tree):
                queue.extend(subtree[1:])
        return subtree

    def set_subtree_bfs(self, index, subtree):
        """ This method replaced the tree with
            the corresponding index by subtree based
            on a breadth-first search.
        """
        if index == 0:
            self[:] = subtree
            return
        queue = deque(izip(repeat(self, len(self[1:])), count(1)))
        total = 0
        while total != index:
            total += 1
            elem = queue.popleft()
            parent = elem[0]
            child  = elem[1]
            if isinstance(parent[child], Tree):
                tree = parent[child]
                queue.extend(izip(repeat(tree, len(tree[1:])), count(1)))
        parent[child] = Tree.rectify_subtree(subtree)        
        

class Fitness(Array):
    '''The fitness is a measure of quality of a solution. The fitness
    inheritates from a python :class:`array.array`, so the number of objectives
    depends on the lenght of the array. The *weights* (defaults to (-1.0,)) 
    argument indicates if the fitness value shall be minimized (negative value)
    or maximized (positive value). The *weights* are also used in
    multi-objective optimization to normalize the fitness.

    Opposed to :class:`Population` and :class:`Individual`, the
    *weights* argument is **not** cycled if it is shorter than the number of
    fitness values. It is extended with its last value.

    Fitnesses may be compared using the ``>``, ``<``, ``>=``, ``<=``, ``==``,
    ``!=`` and :meth:`cmp` operators. The comparison of those operators is made
    lexicographically. Maximization and minimization are taken
    care off by a multiplication between the weights and the fitness values.
    The comparison can be made between fitnesses of different size, if the
    fitnesses are equal until the extra elements, the longer fitness will be
    greater than the shorter.

    .. note::
       When comparing fitness values that are minimized, ``a > b`` will return
       :data:`True` if *a* is inferior to *b*.
    '''
    weights = (-1.0,)
    def __new__(cls, **kargs):
        return super(Fitness, cls).__new__(cls, 'd')

    def __init__(self, values=None):
        if values is not None:
            self.extend(values)

    def isValid(self):
        '''Wheter or not this fitness is valid. An invalid fitness is simply
        an empty array.
        '''
        return len(self) != 0

    def invalidate(self):
        '''Invalidate this fitness. As a matter of facts, it simply deletes
        all the fitness values. This method has to be used after an individual
        is modified.
        '''
        self[:] = array.array('d')

    def isDominated(self, other):
        '''In addition to the comparaison operators that are used to sort
        lexically the fitnesses, this method returns :data:`True` if this
        fitness is dominated by the *other* fitness and :data:`False` otherwise.
        The weights are used to compare minimizing and maximizing fitnesses. If
        there is more fitness values than weights, the las weight get repeated
        until the end of the comparaison.
        '''
        not_equal = False
        # Pad the weights with the last value
        weights = chain(self.weights, repeat(self.weights[-1]))
        for weight, self_value, other_value in zip(weights, self, other):
            self_value = self_value * weight
            other_value = other_value * weight
            if (self_value) > (other_value):
                return False
            elif (self_value) < (other_value):
                not_equal = True
        return not_equal

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __lt__(self, other):
        # Pad the weights with the last value
        weights = chain(self.weights, repeat(self.weights[-1]))
        # Apply the weights to the values
        self_values = array.array('d', imap(operator.mul, self, weights))
        other_values = array.array('d', imap(operator.mul, other, weights))
        # Compare the results
        return self_values < other_values

    def __le__(self, other):
        # Pad the weights with the last value
        weights = chain(self.weights, repeat(self.weights[-1]))
        # Apply the weights to the values
        self_values = array.array('d', imap(operator.mul, self, weights))
        other_values = array.array('d', imap(operator.mul, other, weights))
        # Compare the results
        return self_values <= other_values

    def __eq__(self, other):
        weights = chain(self.weights, repeat(self.weights[-1]))
        # Apply the weights to the values
        self_values = array.array('d', imap(operator.mul, self, weights))
        other_values = array.array('d', imap(operator.mul, other, weights))
        # Compare the results
        return self_values == other_values

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if self > other:
            return 1
        elif other > self:
            return -1
        return 0
    
    def __reduce__(self):
        return (self.__class__, (self.weights,), self.__dict__, iter(self))
    
    
