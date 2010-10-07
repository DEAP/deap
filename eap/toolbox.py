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

"""The :mod:`toolbox` module is intended to contain the operators that you need
in your evolutionary algorithms, from initialisation to evaluation. It is
always possible to use directly the operators from this module but the toolbox
does also contain the default values of the different parameters for each
method. More over, it makes your algorithms easier to understand and modify,
since once an oprerator is set, it can be reused with a simple keyword that
contains all its arguments. Plus, every keyword or argument can be overriden
at all time.

The toolbox is also used in predefined algorithms from the
:mod:`~eap.algorithms` module.
"""

import copy
import functools
import inspect
import math
import random
# Needed by Nondominated sorting
from itertools import chain, cycle
from operator import attrgetter


class Repeat(object):
    """Functional object that repeat a function *func*
    a number of times *times*, then raise a StopIteration
    exception. It implements the Python iterator model.

    This class allows to fill a list with objects produced
    by a function.
    """
    def __init__(self, func, times):
        self.func = func
        self.count = cycle(xrange(times+1))
        self.times = times
        
    def __iter__(self):
        return self
        
    def next(self):
        """Function use to iterate."""
        if self.count.next() == self.times:
            raise StopIteration
        return self.func()
        
class Iterate(object):
    """Class use to cycle on the iterable object
    returned by a function *func*. The function is
    called when there is no longer any possible 
    iteration that can be done on the object.
    """
    def __init__(self, func):
        self.func = func
        self.iter = None
        
    def __iter__(self):
        return self
        
    def next(self):
        """Function use to iterate."""
        try:
            return self.iter.next()
        except StopIteration:
            self.iter = iter(self.func())
            raise StopIteration
        except AttributeError:
            self.iter = iter(self.func())
            return self.iter.next()

class FuncCycle(object):
    """Functionnal object use to cycle and call a 
    list of functions.
    """
    def __init__(self, seq_func):
        self.cycle = cycle(func for func in seq_func)
    def __call__(self):
        return self.cycle.next()()

class Toolbox(object):
    """A toolbox for evolution that contains the evolutionary operators.
    At first the toolbox contains two simple methods. The first method
    :meth:`~eap.toolbox.clone` duplicates any element it is passed as
    argument, this method defaults to the :func:`copy.deepcopy` function.
    The second method :meth:`~eap.toolbox.map` applies the function given
    as first argument to every items of the iterables given as next
    arguments, this method defaults to the :func:`map` function. You may
    populate the toolbox with any other function by using the
    :meth:`~eap.toolbox.register` method.
    """
    
    def __init__(self):
        self.register("clone", copy.deepcopy)
        self.register("map", map)

    def register(self, methodname, method, *args, **kargs):
        """Register a *method* in the toolbox under the name *methodname*. You
        may provide default arguments that will be passed automaticaly when
        calling the registered method.
        
        Keyworded arguments *content_init* and *size_init* may be used to
        simulate iterable initializers. For example, when building objects
        deriving from :class:`list`, the content argument will provide to
        the built list its initial content. Depending on what is given to
        *content_init* and *size_init* the initialization is different. If
        *content_init* is an iterable, then the iterable is consumed enterily
        to intialize each object, in that case *size_init* is not used.
        Otherwise, *content_init* may be a simple function that will be
        repeated *size_init* times in order to fill the object.
        """
        if "content_init" in kargs:
            content = kargs["content_init"]
            del kargs["content_init"]
            if hasattr(content, "__iter__"):
                content = FuncCycle(content)
            if "size_init" in kargs:
                args = list(args)
                args.append(Repeat(content, kargs["size_init"]))
                del kargs["size_init"]
            else:
                args = list(args)
                args.append(Iterate(content))
        pfunc = functools.partial(method, *args, **kargs)
        pfunc.__name__ = method
        setattr(self, methodname, pfunc)
    
    def unregister(self, methodname):
        """Unregister *methodname* from the toolbox."""
        delattr(self, methodname)
        
    def decorate(self, methodname, *decorators):
        """Decorate *methodname* with the specified *decorators*, *methodname*
        has to be a registered function in the current toolbox. Decorate uses
        the signature preserving decoration function
        :func:`~eap.toolbox.decorate`.
        """
        partial_func = getattr(self, methodname)
        method = partial_func.func
        args = partial_func.args
        kargs = partial_func.keywords
        for decorator in decorators:
            method = decorate(decorator)(method)
        setattr(self, methodname, functools.partial(method, *args, **kargs))
        
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
    """Execute a partialy matched crossover (PMX) on the input indviduals.
    The two individuals are modified in place. This crossover expect iterable
    individuals of indices, the result for any other type of individuals is
    unpredictable.

    Moreover, this crossover consists of generating two children by matching
    pairs of values in a certain range of the two parents and swaping the values
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
    """Execute a uniform partialy matched crossover (UPMX) on the input
    indviduals. The two individuals are modified in place. This crossover
    expect iterable individuals of indices, the result for any other type of
    individuals is unpredictable.

    Moreover, this crossover consists of generating two children by matching
    pairs of values chosen at random with a probability of *indpb* in the two
    parents and swaping the values of those indexes. For more details see
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
    """Executes a blend crossover that modify inplace the input individuals.
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
    """Executes a simulated binary crossover that modify inplace the input
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
       resetting the values. Wich way is closer to the representation used
       is up to you.
       
       One easy way to add cronstraint checking to an operator is to 
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
    The *individual* is left intact and the mutant is an independant copy. The
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
    mutant. The *individual* is left intact and the mutant is an independant
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
    s_inds = sorted(individuals, key=attrgetter("fitness"), reverse=True)[:n]
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

def nsga2(individuals, n):
    """Apply NSGA-II selection operator on the *individuals*. Usually,
    the size of *individuals* will be larger than *n* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *n* will have no effect other
    than sorting the population according to a non-domination sheme. The list
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

def spea2(individuals, n):
    """Apply SPEA-II selection operator on the *individuals*. Usually,
    the size of *individuals* will be larger than *n* because any individual
    present in *individuals* will appear in the returned list at most once.
    Having the size of *individuals* equals to *n* will have no effect other
    than sorting the population according to a strength pareto sheme. The list
    returned contains references to the input *individuals*.
    
    For more details on the SPEA-II operator see Zitzler, Laumanns and Thiele,
    "SPEA 2: Improving the strength pareto evolutionary algorithm", 2001.
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
    -- 1). You may pass keyworded arguments to the two selection operators by
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
    
    Using the :mod:`inspect` module, we can retreive the signature of the
    decorated function, what is not possible when not using this method. ::
    
        print inspect.getargspec(myFunc)
        
    It shall return something like ::
    
        (["arg1", "arg2", "arg3"], None, None, ("default",))
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
