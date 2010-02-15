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
or concatenated with other structure. For example a population may contains
individuals or other populations. In the former, the population would behave
as a monodemic evolutionnary algorithm and in the later, as a multidemic
evolutionary algorithm.

The derived structures in the :mod:`base` module are only intended to provide
basic tools to build simple evolutionary algorithm and much more complex complex
structures may be developed, in wich case we are strongly interested to add
those complex structures to the library.
'''

import array
import copy
import itertools
import operator
import random
import sys

#class Population(object):
#    '''A population is an empty :class:`~eap.observable.Observable` object. The
#    population object is more of a base class than an intanciable class
#    as it is not a container.'''
#    def __init__(self):
#        pass


class Population(list):
    '''A population inherits from the python's base type :class:`list` for its
    iterable properties. There is two way of initialising a list population;
    first by creating it without any arguments and appending the objects that it
    shall contains with the :meth:`append` method and second by setting its size
    to a positive integer and giving it a *generator* that when called
    :meth:`generator` will return the object that will be appended.

    The *generator* may also be a list of generators that will be cycled
    throught until the population has reached its size. For example, ::

        >>> def generatorA():
        ...     return 'Ind-A'
        ...
        >>> def generatorB():
        ...     return 'Ind-B'
        ...
        >>> pop = Population(size=5, generator=[generatorA, generatorB])

    will produce a :class:`Population` ::

        >>> print pop
        ['Ind-A', 'Ind-B', 'Ind-A', 'Ind-B', 'Ind-A']

    A population may be copied using the :meth:`copy.copy` method.
    The copy produced is a mix of deep copy and shallow copy. All the attributes
    of the population are shallow copied, even if an attribute has been added at
    runtime. The list of objects is copied by calling :meth:`copy.copy` on each
    element. If you have for example a population of populations of integers,
    the integers will be deeply copied.
    '''
    def __init__(self, size=0, generator=None):
        try:
            self.extend([generator() for i in xrange(size)])
        except TypeError:
            lLength = len(generator)
            self.extend(generator[i % lLength]() for i in xrange(size))

    def __copy__(self):
        lCopy = self.__class__.__new__(self.__class__)
        lCopy.__dict__.update(self.__dict__)
        lCopy[:] = map(copy.copy, self)


class PopulationMatrix(Population):
    '''The matrix population is much similar to the :class:`Population`, it
    only defines some more specific access methods to retreive the informations.
    The only difference is that the matrix population is filled row by
    row in a way that giving a list of generators will produce the following
    result. ::

        >>> def generatorA():
        ...     return 'Ind-A'
        ...
        >>> def generatorB():
        ...     return 'Ind-B'
        ...
        >>> MatrixPopulation(rows=2, columns=3, generator=[generatorA, generatorB])
        +---------+---------+---------+
        | 'Ind-A' | 'Ind-B' | 'Ind-A' |
        +---------+---------+---------+
        | 'Ind-B' | 'Ind-A' | 'Ind-B' |
        +---------+---------+---------+

    Internaly the matrix population is simply a :class:`list`.
    '''
    def __init__(self, rows=0, columns=0, generator=None):
        Population.__init__(self, rows * columns, generator)

    def row(self, row):
        '''Return a specific row of the matrix population.'''
        return self[(row * self.mNumCols):(row * (self.mNumCols + 1))]

    def col(self, column):
        '''Return a specific column of the matrix population.'''
        lCol = []
        for i in range(self.mNumRows):
            lCol.append(self[i * self.mNumCols + column])
            print lCol
        return lCol

    def get(self, row, column):
        '''Return a specific element by its position in the matrix population.'''
        return self[row * self.mNumCols + column]


#class Individual(object):
#    '''An individual is an :class:`~eap.observable.Observable` object
#    associated with a fitness. As the :class:`Population`, the basic
#    individual is not a container of any type. If a *fitness* is passed
#    to a individual then it may be both; an object generator that when called
#    :meth:`fitness` returns an object or an already constructed object. In both
#    cases the object will be stored as is in the :attr:`mFitness` attribute of
#    the individual. This allows both following methods to be used. ::
#
#        >>> def fitness():
#        ...    return 'fit-A'
#        ...
#        >>> Individual(fitness=fitness)
#        >>> Individual(fitness=fitness())
#
#    '''
#    def __init__(self, fitness=None):
#        if fitness is not None:
#            try:        # For conveniance, the user may pass a fitness object
#                self.mFitness = fitness()
#            except TypeError:
#                self.mFitness = fitness


class Individual(list):
    '''An individual inherits from  the python's base type :class:`list` for its
    container properties. There is two way of initialising a list individual;
    first by creating it without any arguments and appending the objects that it
    shall contains with the :meth:`append` method and second by setting its size
    to a positive integer and giving it a *generator* that when called
    :meth:`generator.next` will return the object that will be appended. The
    fitness argument is passed to the :class:`Individual`.
    
    Opposed to the :class:`Population` the individual uses generator
    functions to produce its attributes. This kind of function allows a greater
    flexibility when it comes to produce interrelated objects like vector of
    indices.

    The *generator* may also be a list of generator functions that will be
    cycled throught until the individual has reached its size. For example, ::

        >>> def generatorA():
        ...     while True:
        ...         yield 'Attr-A'
        ...
        >>> def generatorB():
        ...     while True:
        ...         yield 'Attr-B'
        ...
        >>> ind = Individual(size=5, generator=[generatorA, generatorB])

    will produce a :class:`Individual` ::

        >>> print ind
        ['Attr-A', 'Attr-B', 'Attr-A', 'Attr-B', 'Attr-A']

    An individual may be copied using the :meth:`copy.copy` method.
    The copy produced is a mix of deep copy and shallow copy. All the attributes
    of the individual are shallow copied, even if an attribute has been added
    at run time. The list of objects is copied by calling :meth:`copy.copy` on
    each element. If you have for example a list individual of objects that
    defines a method :meth:`__copy__` to copy the object's attributes, 
    the objects will be deeply copied.
    '''
    def __init__(self, size=0, generator=None, fitness=None):
        if fitness is not None:
            try:        # For conveniance, the user may pass a fitness object
                self.mFitness = fitness()
            except TypeError:
                self.mFitness = fitness

        try:
            self.extend([generator.next() for i in xrange(size)])
        except TypeError:
            lCycle = itertools.cycle(generator)
            self.extend([lCycle.next().next() for i in xrange(size)])

    def __copy__(self):
        """This method makes a shallow copy of self and fitness and then a deep
        copy of the list of objects that it is made of using
        :meth:`copy.copy` for the fitness and :meth:`clone` for the elements
        that are in its list.

        .. warning::
           If you override this class be sure that all elements are
           copied the way that they should.

        """
        lCopy = self.__new__(self.__class__)
        lCopy.__dict__.update(self.__dict__)
        lCopy.mFitness = copy.copy(self.mFitness)
        lCopy[:] = map(copy.copy, self)
        return lCopy

    def __repr__(self):
        return str(list(self)) + ' : ' + str(self.mFitness)

class IndividualTree(list):
    
    def __init__(self, generator=None, fitness=None):
        if fitness is not None:
            try:        # For convenience, the user may pass a fitness object
                self.mFitness = fitness()
            except TypeError:
                self.mFitness = fitness
        self[:] = generator.next()

    @staticmethod
    def count(tree):
        if isinstance(tree, list):
            value = 0
            for node in tree:
                value += IndividualTree.count(node)
            return value
        else:
            return 1

    @staticmethod
    def evaluateExpr(expr):
        try:
            func = expr[0]
            try:
                return func(*[IndividualTree.evaluateExpr(value) for value in expr[1:]])
            except TypeError:
                return func(*expr[1:])
        except TypeError:
            try:
                return expr()
            except TypeError:
                return expr

    def getSubTree(self, index):
        def __getSubTree(tree, index):
            total = 0
            if index == 0:
                return tree
            for child in tree:
                if total == index:
                   return child
                nbrChild = IndividualTree.count(child)
                if nbrChild + total > index:
                    return __getSubTree(child, index-total)
                else:
                    total += nbrChild
        return __getSubTree(self, index)

    def setSubTree(self, index, subTree):
        def __setSubTree(tree, index, subTree):
            total = 0
            for i, child in enumerate(tree):
                if total == index:
                    tree[i] = subTree
                    return
                if IndividualTree.count(child) + total > index:
                    __setSubTree(child, index-total, subTree)
                    return
                else:
                    total += IndividualTree.count(child)
        __setSubTree(self, index, subTree)

    def __len__(self):
        return IndividualTree.count(self)

    def __copy__(self):
        lCopy = self.__new__(self.__class__)
        lCopy.__dict__.update(self.__dict__)
        lCopy.mFitness = copy.copy(self.mFitness)
        lCopy[:] = map(copy.deepcopy, self)
        return lCopy

    def evaluate(self):
        return IndividualTree.evaluateExpr(self)

    def __repr__(self):
        return str(self.evaluate()) + ' : ' + str(self.mFitness)

#class IndicesIndividual(Individual, list):
#    """
#    """
#    def __init__(self, size, fitness):
#        Individual.__init__(self, fitness)
#        for i in xrange(size):
#            self.append(i)
#        random.shuffle(self)


class Fitness(array.array):
    '''The fitness is a measure of quality of a solution. The fitness
    inheritates from a python :class:`array.array`, so the number of objectives
    depends on the lenght of the array. The *weights* (defaults to (-1.0,)) 
    argument indicates if the fitness value shall be minimized (negative value)
    or maximized (positive value). The *weights* are also used in
    multi-objective optimization to normalize the fitness.

    Opposed to :class:`ListPopulation` and :class:`ListIndividual`, the
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
    def __new__(cls, *args, **kargs):
        return super(Fitness, cls).__new__(cls, 'd')

    def __init__(self, weights=(-1.0,)):
        self.mWeights = array.array('d', weights)

    def isValid(self):
        '''Wheter or not this fitness is valid. An invalid fitness is simply
        an empty array.
        '''
        return len(self) != 0

    def setInvalid(self):
        '''Invalidate this fitness. As a matter of facts, it simply deletes
        all the fitness values. This method has to be used after an individual
        is modified.
        '''
        self[:] = array.array('d')

    def isDominated(self, other):
        '''In addition to the comparaison operators that are used to sort
        lexically the fitnesses, this method returns :data:`True` if this fitness
        is dominated by the *other* fitness and false otherwise. Once again,
        the weights are used in this function.
        '''
        lNotEqual = False;
        for lSVal, lSWght, lOVal, lOWght in zip(self, self.mWeights, other, other.mWeights):
            lSelfFit = lSVal * lSWght
            lOtherFit = lOVal * lOWght
            if (lSelfFit) > (lOtherFit):
                return False
            elif (lSelfFit) < (lOtherFit):
                lNotEqual = True
        return lNotEqual

    def __gt__(self, other):
        return not self.__le__(other)

    def __ge__(self, other):
        return not self.__lt__(other)

    def __lt__(self, other):
        # Pad the weights with the last value
        lSelfWeights = itertools.chain(self.mWeights,
                                       itertools.repeat(self.mWeights[-1]))
        lOtherWeights = itertools.chain(other.mWeights,
                                        itertools.repeat(other.mWeights[-1]))
        # Apply the weights to the values
        lSelfValues = array.array('d', itertools.imap(operator.mul,
                                                      self, lSelfWeights))
        lOtherValues = array.array('d', itertools.imap(operator.mul,
                                                       other, lOtherWeights))
        # Compare the results
        return lSelfValues < lOtherValues

    def __le__(self, other):
        # Pad the weights with the last value
        lSelfWeights = itertools.chain(self.mWeights,
                                       itertools.repeat(self.mWeights[-1]))
        lOtherWeights = itertools.chain(other.mWeights,
                                        itertools.repeat(other.mWeights[-1]))
        # Apply the weights to the values
        lSelfValues = array.array('d', itertools.imap(operator.mul,
                                                      self, lSelfWeights))
        lOtherValues = array.array('d', itertools.imap(operator.mul,
                                                       other, lOtherWeights))
        # Compare the results
        return lSelfValues <= lOtherValues

    def __eq__(self, other):
        # Pad the weights with the last value
        lSelfWeights = itertools.chain(self.mWeights,
                                       itertools.repeat(self.mWeights[-1]))
        lOtherWeights = itertools.chain(other.mWeights,
                                        itertools.repeat(other.mWeights[-1]))
        # Apply the weights to the values
        lSelfValues = array.array('d', itertools.imap(operator.mul,
                                                      self, lSelfWeights))
        lOtherValues = array.array('d', itertools.imap(operator.mul,
                                                       other, lOtherWeights))
        # Compare the results
        return lSelfValues == lOtherValues

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if self > other:
            return 1
        elif other > self:
            return -1
        return 0

    def __repr__(self):
        return str(list(self))

    def __reduce__(self):
        return (self.__class__, (self.mWeights,), self.__dict__, iter(self))

    def __copy__(self):
        lCopy = self.__new__(self.__class__)
        lCopy.__dict__.update(self.__dict__)
        lCopy.extend(self)
        lCopy.mWeights[:] = self.mWeights[:]
        return lCopy


def realGenerator(min=0.0, max=1.0):
    '''A generator function to build a real valued attributes between *min*
    (defaults to 0.0) and *max* (defaults to 1.0). The start point is always
    included. The end point *max* may or may not be included depending on the
    random number generator used, see python's :mod:`random` module for more
    details.

    This function use the :meth:`uniform` method from the python base
    :mod:`random` module.
    '''
    while 1:
        yield random.uniform(min, max)


def integerGenerator(min=0, max=sys.maxint):
    '''A generator function to build a integer valued attributes between *min*
    and *max*. The start and end points are always included.

    This function use the :meth:`randint` method from the python base
    :mod:`random` module.
    '''
    while 1:
        yield random.randint(min, max)


def indiceGenerator(max):
    '''A generator function to build indice valued sequences between 0 and
    *max*. Series of *max* - 1 calls to this generator shall never return the
    same integer twice. The sequence is reinitialized (in a different order) at
    the *max*\ th call.

    It is possible to force the reinitialization of the sequence by sending
    :data:`True` to this generator via the :meth:`send` method.

    This function use the :meth:`shuffle` method from the python base
    :mod:`random` module.
    '''
    lIndices = []
    lReset = False
    while 1:
        if len(lIndices) == 0 or lReset is True:
            lReset = False
            lIndices = range(max)
            random.shuffle(lIndices)
        lReset = yield lIndices.pop(0)


def booleanGenerator():
    '''A generator function to build a boolean valued attributes.

    This function use the :meth:`choice` method from the python base
    :mod:`random` module.
    '''
    while 1:
        yield random.choice([False, True])

def expressionGenerator(funcSet, termSet, maxDepth):
    def arity(func):
        return func.func_code.co_argcount
    def __expressionGenerator(funcSet, termSet, maxDepth):
        if maxDepth == 0 or random.random() < len(termSet)/(len(termSet)+len(funcSet)):
            expr = random.choice(termSet)
            try:
                expr = expr()
            except:
                pass
        else:
            lFunc = random.choice(funcSet)
            lArgs = [__expressionGenerator(funcSet, termSet, maxDepth-1) for i in xrange(arity(lFunc))]
            expr = [lFunc]
            expr.extend(lArgs)
        return expr
    while True:
        lMaxDepth = maxDepth
        try:
             lMaxDepth = random.randint(maxDepth[0], maxDepth[1])
        except TypeError:
            pass
        yield __expressionGenerator(funcSet, termSet, lMaxDepth)