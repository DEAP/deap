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

"""The :mod:`~eap.base` module provides basic structures to build evolutionary
algorithms.
"""

import array
import copy
import operator
import random

from collections import deque
from itertools import izip, repeat, count, chain, imap
import itertools

class List(list):
    """A List is a basic container that inherits from the python :class:`list`
    class. The only difference is that it may be initialized using three
    methods, a callable object, an iterable object or a generator function (the
    last two initialization methods are the same but both are mentionned
    in order to emphasize their presence). The first method is to provide a
    callable object that return the desired value, the method will be
    called *size* times and the returned valued will be appended to the
    list after each call. The most classic way to initialize a List is to
    provide a :data:`lambda` function using a random method, for instance, ::
    
        print List(size=3, content=lambda: random.choice((True, False)))
        [False, False, True]
    
    A similar way is to provide the *content* argument with a class. For 
    example, lets build a simple
    :class:`MyTuple` class that initialize a tuple of boolean and integer
    in its member values ::
    
        class MyTuple(object):
            calls = 0
            def __init__(self):
                self.values = bool(self.calls), calls
                self.__class__.calls += 1
            def __repr__(self):
                return repr(self.values)
    
    Initializing a list of 3 :class:`MyTuples` is done by ::
    
        print List(size=3, content=MyTuple)
        [(False, 0), (True, 1), (True, 2)]
        
    The same result may be obtained by providing an iterable to the List's
    *content*, in that case, no *size* is needed since the size will be that
    same as the iterable provided. ::
    
        print List(content=[MyTuple(), MyTuple(), MyTuple()])
        [(False, 0), (True, 1), (True, 2)]
        
    The same thing may be achieved by the uses of a generator function. First 
    the generator must be defined ::
    
        def myGenerator(size):
            for i in xrange(size):
                yield MyTuple()
            raise StopIteration
            
    Then it must be initialized and passed to List's *content* ::
    
         print List(content=myGenerator(size=3))
         [(False, 0), (True, 1), (True, 2)]
    """
    def __init__(self, size=0, content=None):
        if content is not None:
            if callable(content):
                self.extend(content() for i in xrange(size))
            else:
                self.extend(content)

class Array(array.array):
    """An Array is a basic container that inherits from the python
    :class:`~array.array` class. The Array may be
    initialized  by the exact three methods than the :class:`List`. When
    initializing an Array, a *typecode* must be provided to build the right
    type of array. The *typecode* must be one of the type codes listed in
    the python :mod:`array` module.
    """
    def __new__(cls, typecode, content=[], size=0):
        gen_content = content
        if callable(content):
            gen_content = (content() for i in xrange(size))
        return super(Array, cls).__new__(cls, typecode, gen_content)
        
    def __init__(self):
        pass

#    def __init__(self, size=0, content=None):
#        if content is not None:
#            if callable(content):
#                self.extend(content() for i in xrange(size))
#            else:
#                self.extend(content)

    def __deepcopy__(self, memo):
        """Overrides the deepcopy from array.array that does not copy the
        object's attributes.
        """
        cls = self.__class__
        copy_ = cls.__new__(cls, typecode=self.typecode)
        memo[id(self)] = copy_
        copy_.__dict__.update(copy.deepcopy(self.__dict__, memo))
        copy_.extend(self)
        return copy_

class Indices(Array):
    """An Indices is a specialization of the :class:`Array` container, 
    it contains only integers (type code ``"i"``) between 0 and *size* - 1 and
    do not repeat the same integer twice. For example, ::
    
        print Indices(size=5)
        array('i', [0, 4, 2, 3, 1])
        
    is the same than providing the *content* ``[0, 4, 2, 3, 1]`` and the
    *type code* ``"i"`` to an :class:`Array`. The Indices class is provided
    only for convenience.
    """
    def __new__(cls, typecode="i", content=[], size=0):
        return super(Indices, cls).__new__(cls, "i", content, size)
    
    def __init__(self, size=0):
        self.extend(i for i in xrange(size))
        random.shuffle(self)
        
class Tree(list):
    """ Basic N-ary tree class"""
    @classmethod
    def create_node(cls, obj):
        Node = type("Node", (obj.__class__,), {})
        Node.height = property(lambda self: 0)
        Node.size = property(lambda self: 1)
        Node.root = property(lambda self: self)
        new_node = Node.__new__(Node)
        new_node.__dict__.update(obj.__dict__)          
        return new_node

    @classmethod
    def rectify_subtree(cls, subtree):
        if subtree.size > 1:
            return subtree
        else:
            return subtree.root

    def __init__(self, content=None):
        list.__init__(self)
        if hasattr(content, "__call__"):
            content = content()
        for elem in content:
            if isinstance(elem, list):
                self.append(Tree(elem))
            else:
                self.append(Tree.create_node(elem))
    
    @property
    def root(self):
        return self[0]

    @property
    def size(self):
        """ This method returns the number of nodes in the tree."""
        return sum(elem.size for elem in self)

    @property
    def height(self):
        """ This method returns the height of the tree."""
        return max(elem.height for elem in self)+1

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
            nbr_child = child.size
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
            nbr_child = child.size
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
    """The fitness is a measure of quality of a solution. The fitness
    inheritates from the :class:`Array` class, so the number of objectives
    depends on the lenght of the array.

    Fitnesses may be compared using the ``>``, ``<``, ``>=``, ``<=``, ``==``,
    ``!=`` and :meth:`cmp` operators. The comparison of those operators is made
    lexicographically. Maximization and minimization are taken
    care off by a multiplication between the :attr:`weights` and the fitness values.
    The comparison can be made between fitnesses of different size, if the
    fitnesses are equal until the extra elements, the longer fitness will be
    superior to the shorter.

    .. note::
       When comparing fitness values that are minimized, ``a > b`` will return
       :data:`True` if *a* is inferior to *b*.
    """
    
    weights = (-1.0,)
    """The weights are used in the fitness comparison. They are shared among
    all fitnesses of the same type.
    This member is **not** meant to be manipulated since it may influence how
    fitnesses are compared and may
    result in undesirable effects. However if you wish to manipulate it, in 
    order to make the change effective to all fitnesses of the same type, use
    ``FitnessType.weights = new_weights`` or
    ``self.__class__.weights = new_weights`` or from an individual
    ``ind.fitness.__class__.weights = new_weights``.
    """
    
    def __new__(cls, typecode="d", values=None):
        return super(Fitness, cls).__new__(cls, "d")

    def __init__(self, values=None):
        if values is not None:
            self.extend(values)
        
    def getvalid(self):
        return len(self) != 0
    
    def setvalid(self, value):
        if not value:
            self[:] = array.array("d")

    valid = property(getvalid, setvalid, None, 
                     "Asses if a fitness is valid or not.")

#    def isValid(self):
#        '''Wheter or not this fitness is valid. An invalid fitness is simply
#        an empty array.
#        '''
#        return len(self) != 0
#
#    def invalidate(self):
#        '''Invalidate this fitness. As a matter of facts, it simply deletes
#        all the fitness values. This method has to be used after an individual
#        is modified, usualy it is done in the modification operator.
#        '''
#        self[:] = array.array('d')

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
#        weights = itertools.chain(self.weights, repeat(self.weights[-1]))
        for weight, self_value, other_value in izip(self.weights, self, other):
            self_w_value = self_value * weight
            other_w_value = other_value * weight
            if (self_w_value) > (other_w_value):
                return False
            elif (self_w_value) < (other_w_value):
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
        
