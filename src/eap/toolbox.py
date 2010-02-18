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

'''The :mod:`toolbox` module is intended to contain the operators that you need
in your evolutionary algorithms, from initialisation to evaluation. It is
always possible to use directly the operators from this module but the toolbox
does also contain the default values of the different parameters for each
method. More over, it makes your algorithms easier to understand and modify,
since once an oprerator is set, it can be reused with a simple keyword that
conatins all its arguments. Plus, every keyword or argument can be overriden
at all time.

The toolbox is also used in predefined algorithms from the :mod:`algorithms`
module.
'''

import copy
from functools import partial
import math
import random

class Toolbox(object):
    '''A toolbox for evolution that contains the evolutionary operators.
    At first this toolbox is empty, you can populate it by using the method
    :meth:`register`.
    '''

    def register(self, methodName, method, *args, **kargs):
        '''Register an operator in the toolbox.'''
        setattr(self, methodName, partial(method, *args, **kargs))

    def unregister(self, methodName):
        '''Unregister an operator from the toolbox.'''
        delattr(self, methodName)


######################################
# GA Crossovers                      #
######################################

def twoPointsCx(indOne, indTwo):
    '''Execute a two points crossover on the input individuals. The two children
    produced are returned as a tuple, the two parents are left intact.
    This operation apply on a :class:`ListIndividual` without restriction.
    Whatever the passed individuals are, they are gonna be mixed like follow ::

        >>> ind1 = [A(1), ..., A(n), ..., A(n+i), ..., A(m)]
        >>> ind2 = [B(1), ..., B(n), ..., B(n+i), ..., B(k)]
        >>> # Crossover with mating points n and n+i, n > 1 and n+i <= min(m, k)
        >>> child1, child2 = twoPointsCx(ind1, ind2)
        >>> print child1
        [A(1), ..., B(n), ..., B(n+i-1), A(n+i), ..., A(m)]
        >>> print child2
        [B(1), ..., A(n), ..., A(n+i-1), B(n+i), ..., B(k)]

    This function use the :func:`randint` function from the python base
    :mod:`random` module.
    '''
    lSize = min(len(indOne), len(indTwo))
    lChild1, lChild2 = copy.copy(indOne), copy.copy(indTwo)
    lCxPoint1 = random.randint(1, lSize)
    lCxPoint2 = random.randint(1, lSize - 1)

    if lCxPoint2 >= lCxPoint1:
        lCxPoint2 += 1
    else:			# Swap the two cx points
        lCxPoint1, lCxPoint2 = lCxPoint2, lCxPoint1

    lChild1[lCxPoint1:lCxPoint2], lChild2[lCxPoint1:lCxPoint2] \
         = lChild2[lCxPoint1:lCxPoint2], lChild1[lCxPoint1:lCxPoint2]
    try:
        lChild1.mFitness.invalidate()
        lChild2.mFitness.invalidate()
    except AttributeError:
        pass
    return lChild1, lChild2


def onePointCx(indOne, indTwo):
    '''Execute a one point crossover on the input individuals. The two children
    produced are returned as a tuple, the two parents are left intact.
    This operation apply on a :class:`ListIndividual` without restriction.
    Whatever the passed individuals are, they are gonna be mixed like follow ::

        >>> ind1 = [A(1), ..., A(n), ..., A(m)]
        >>> ind2 = [B(1), ..., B(n), ..., B(k)]
        >>> # Crossover with mating point n, 1 < n <= min(m, k)
        >>> child1, child2 = twoPointsCx(ind1, ind2)
        >>> print child1
        [A(1), ..., B(n), ..., B(k)]
        >>> print child2
        [B(1), ..., A(n), ..., A(m)]

    This function use the :func:`randint` function from the python base
    :mod:`random` module.
    '''
    lSize = min(len(indOne), len(indTwo))
    lChild1, lChild2 = copy.copy(indOne), copy.copy(indTwo)
    lCxPoint = random.randint(1, lSize - 1)
    lChild1[lCxPoint:], lChild2[lCxPoint:] = lChild2[lCxPoint:], lChild1[lCxPoint:]
    try:
        lChild1.mFitness.invalidate()
        lChild2.mFitness.invalidate()
    except AttributeError:
        pass
    return lChild1, lChild2

def pmCx(indOne, indTwo):
    '''Execute a partialy matched crossover on the input indviduals. The two
    childrens produced are returned as a tuple, the two parents are left intact.
    This crossover expect individuals of indices, the result for any other type
    of individuals is unpredictable.

    Moreover, this crossover consists of generating two children by matching
    pairs of values in a certain range of the two parents and swaping the values
    of those indexes. For more details see Goldberg and Lingel, "Alleles,
    loci, and the traveling salesman problem", 1985.

    For example, the following parents will produce the two following childrens
    when mated with crossover points ``a = 2`` and ``b = 3``. ::

        >>> ind1 = [0, 1, 2, 3, 4]
        >>> ind2 = [1, 2, 3, 4, 0]
        >>> child1, child2 = pmxCx(ind1, ind2)
        >>> print child1
        [0, 2, 3, 1, 4]
        >>> print child2
        [2, 3, 1, 4, 0]

    This function use the :func:`randint` function from the python base
    :mod:`random` module.
    '''
    lChild1, lChild2 = copy.copy(indOne), copy.copy(indTwo)
    lSize = min(len(indOne), len(indTwo))
    lPos1, lPos2 = [0]*lSize, [0]*lSize
    # Initialize the position of each indices in the individuals
    for i in xrange(lSize):
        lPos1[lChild1[i]] = i
        lPos2[lChild2[i]] = i
    # Choose crossover points
    lCXPoint1 = random.randint(0, lSize)
    lCXPoint2 = random.randint(0, lSize - 1)
    if lCXPoint2 >= lCXPoint1:
        lCXPoint2 += 1
    else:			# Swap the two cx points
        lCXPoint1, lCXPoint2 = lCXPoint2, lCXPoint1
    # Apply crossover between cx points
    for i in xrange(lCXPoint1, lCXPoint2):
        # Keep track of the selected values
        lTemp1 = lChild1[i]
        lTemp2 = lChild2[i]
        # Swap the matched value
        lChild1[i], lChild1[lPos1[lTemp2]] = lTemp2, lTemp1
        lChild2[i], lChild2[lPos2[lTemp1]] = lTemp1, lTemp2
        # Position bookkeeping
        #print lTemp1, lTemp2
        lPos1[lTemp1], lPos1[lTemp2] = lPos1[lTemp2], lPos1[lTemp1]
        lPos2[lTemp1], lPos2[lTemp2] = lPos2[lTemp2], lPos2[lTemp1]
        #print lPos1

    try:
        lChild1.mFitness.invalidate()
        lChild2.mFitness.invalidate()
    except AttributeError:
        pass
    return lChild1, lChild2


def blendESCx(indOne, indTwo, alpha):
    lChild1, lChild2 = copy.copy(indOne), copy.copy(indTwo)
    lLenght = min(len(lChild1), len(lChild2))
    for i in xrange(lLenght):
        lU_xi = random.random()
        lGamma_xi = ((1.0 + 2.0 * alpha) * lU_xi) - alpha
        lU_si = random.random()
        lGamma_si = ((1.0 + 2.0 * alpha) * lU_si) - alpha
        lX1_i = lChild1[i][0]
        lX2_i = lChild2[i][0]
        lS1_i = lChild1[i][1]
        lS2_i = lChild2[i][1]

        lChild1[i][0] = (1.0 - lGamma_xi) * lX1_i + lGamma_xi * lX2_i
        lChild2[i][0] = (1.0 - lGamma_xi) * lX2_i + lGamma_xi * lX1_i
        # TODO : add some constraint checking !
        lChild1[i][1] = (1.0 - lGamma_si) * lS1_i + lGamma_si * lS2_i
        lChild2[i][1] = (1.0 - lGamma_si) * lS2_i + lGamma_si * lS1_i
    
    try:
        lChild1.mFitness.invalidate()
        lChild2.mFitness.invalidate()
    except AttributeError:
        pass
    return lChild1, lChild2


######################################
# GA Mutations                       #
######################################

def gaussMut(individual, mu, sigma, mutIndxPb, min, max):
    '''This function applies a gaussian mutation on the input individual and
    returns the mutant. The *individual* is left intact and the mutant is an
    independant copy. This mutation expects an iterable individual composed of
    real valued attributes. The *mutIndxPb* argument is the probability of each
    attribute to be mutated.

    .. todo::
       Add a parameter acting as constraints for the real valued attribute so
       a min, max and interval may be used.

    This function uses the :func:`random` and :func:`gauss` functions from the
    python base :mod:`random` module.
    '''
    lMutated = False
    lIndividual = copy.copy(individual)
    for i in xrange(len(lIndividual)):
        if random.random() < mutIndxPb:
            lIndividual[i] += random.gauss(mu, sigma)
            # TODO : add some constraint checking with an object!!
            if lIndividual[i] < min:
                lIndividual[i] = min
            elif lIndividual[i] > max:
                lIndividual[i] = max
            lMutated = True
    if lMutated:
        try:
            lIndividual.mFitness.invalidate()
        except AttributeError:
            pass
    return lIndividual


def gaussESMut(individual, mutIndxPb):
    '''This function applies a gaussian mutation on the input evolution strategy
    individual and
    returns the mutant. The *individual* is left intact and the mutant is an
    independant copy. This mutation expects an iterable individual composed of
    paired [value, strategy] attributes. The *mutIndxPb* argument is the
    probability of each attribute to be mutated.

    .. todo::
       Add a parameter acting as constraints for the real valued attribute so
       a min, max and interval may be used.

    This function uses the :func:`random` and :func:`gauss` functions from the
    python base :mod:`random` module.
    '''
    lMutated = False
    lIndividual = copy.copy(individual)
    lLenght = len(lIndividual)
    lT = 1.0 / math.sqrt(2.0 * math.sqrt(lLenght))
    lTPrime = 1.0 / math.sqrt(2.0 * lLenght)
    lN = random.gauss(0.0, 1.0)
    # TODO : add some constraint checking !!
    lMinStrategy = 0.01
    for i in xrange(len(lIndividual)):
        if random.random() < mutIndxPb:
            lNi = random.gauss(0.0, 1.0)

            lIndividual[i][1] *= math.exp(lTPrime * lN + lT * lNi)
            if lIndividual[i][1] < lMinStrategy:
                lIndividual[i][1] = lMinStrategy


            lIndividual[i][0] += lIndividual[i][1] * lNi
            # TODO : add some constraint checking !!
            lMutated = True
    if lMutated:
        try:
            lIndividual.mFitness.invalidate()
        except AttributeError:
            pass
    return lIndividual


def shuffleIndxMut(individual, shuffleIndxPb):
    '''Shuffle the attributes of the input individual and return the mutant.
    The *individual* is left intact and the mutant is an independant copy. The
    *individual* is expected to be iterable. The *shuffleIndxPb* argument is the
    probability of each attribute to be moved.

    This function uses the :func:`random` and :func:`randint` functions from the
    python base :mod:`random` module.
    '''
    lMutated = False
    lIndividual = copy.copy(individual)
    lSize = len(lIndividual)
    for i in range(lSize):
        if random.random() < shuffleIndxPb:
            lSwapIndx = random.randint(0, lSize - 2)
            if lSwapIndx >= i:
                lSwapIndx += 1
            lIndividual[i], lIndividual[lSwapIndx] = \
                lIndividual[lSwapIndx], lIndividual[i]
            lMutated = True
    if lMutated:
        try:
            lIndividual.mFitness.invalidate()
        except AttributeError:
            pass
    return lIndividual


def flipBitMut(individual, flipIndxPb):
    '''Flip the value of the attributes of the input individual and return the
    mutant. The *individual* is left intact and the mutant is an independant
    copy. The *individual* is expected to be iterable and the values of the
    attributes shall stay valid after the ``not`` operator is called on them.
    The *flipIndxPb* argument is the probability of each attribute to be
    flipped.

    This function uses the :func:`random` function from the python base
    :mod:`random` module.
    '''
    lMutated = False
    lIndividual = copy.copy(individual)
    for lGeneIndx in xrange(len(lIndividual)):
        if random.random() < flipIndxPb:
            lIndividual[lGeneIndx] = not lIndividual[lGeneIndx]
            lMutated = True
    if lMutated:
        try:
            lIndividual.mFitness.invalidate()
        except AttributeError:
            pass

    return lIndividual

######################################
# GP Crossovers                      #
######################################

def onePtCxGP(indOne, indTwo):
    def chooseSubTree(expr1, expr2):
	try:
	    index = random.randint(1,min([len(expr1), len(expr2)])-1)
        except TypeError:
	    return None, None, None
        
        if random.random() < 0.5:
            lRetIndex, lSub1, lSub2 = chooseSubTree(expr1[index], expr2[index])
            if lRetIndex is not None:
                return lRetIndex, lSub1, lSub2
        return index, expr1, expr2


    lChild1, lChild2 = copy.copy(indOne), copy.copy(indTwo)
    index, lSub1, lSub2 = chooseSubTree(lChild1, lChild2)
    lSub1[index], lSub2[index] = lSub2[index], lSub1[index]

    try:
        lChild1.mFitness.invalidate()
        lChild2.mFitness.invalidate()
    except AttributeError:
        pass

    return lChild1, lChild2

def uniformOnePtCxGP(indOne, indTwo):

    index = random.randint(1,min([len(indOne), len(indTwo)])-1)

    lChild1, lChild2 = copy.copy(indOne), copy.copy(indTwo)

    lChild1.setSubTree(indTwo.getSubTree(index),index)
    lChild2.setSubTree(indOne.getSubTree(index),index)
    try:
        lChild1.mFitness.invalidate()
        lChild2.mFitness.invalidate()
    except AttributeError:
        pass
    return lChild1, lChild2

######################################
# GP Mutations                       #
######################################

def subTreeMut(individual, treeGenerator, depthRange):
    def chooseSubTree(expr):
	try:
	    index = random.randint(1,len(expr)-1)
	except TypeError:
	    return None, None

        if random.random() < 0.5:
            ret_val, sub_tree = chooseSubTree(expr[index])
            if ret_val is not None:
                return ret_val, sub_tree
        return index, expr

    lIndividual = copy.copy(individual)
    index, sub = chooseSubTree(lIndividual)
    subExprGen = treeGenerator(maxDepth=depthRange)
    sub[index] = subExprGen.next()
    try:
        lIndividual.mFitness.invalidate()
    except AtributeError:
        pass
    return lIndividual

def uniformTreeMut(individual, treeGenerator, depthRange):

    lIndividual = copy.copy(individual)
    index = random.randint(1, len(lIndividual)-1)
    subExprGen = treeGenerator(maxDepth=depthRange)
    lIndividual.setSubTree(index, subExprGen.next())
    try:
        lIndividual.mFitness.invalidate()
    except AtributeError:
        pass
    return lIndividual


######################################
# Selections                         #
######################################

def rndSel(individuals, n):
    '''Select *n* individuals at random from the input *individuals*. The
    list returned contains shallow copies of the input *individuals*. That
    means if an individual is selected twice, modifying one of the two
    occurences will modify the other.

    .. versionchanged:: 0.3.1a
       Removed random sample without replacement as this is simply a call to
       python's :func:`random.sample` function

    This function uses the :func:`choice` function from the
    python base :mod:`random` module.
    '''
    return [random.choice(individuals) for i in xrange(n)]


def bestSel(individuals, n):
    '''Select the *n* best individuals among the input *individuals*. The
    list returned contains shallow copies of the input *individuals*.
    '''
    return sorted(individuals, key=lambda ind : ind.mFitness, reverse=True)[:n]


def worstSel(individuals, n):
    '''Select the *n* worst individuals among the input *individuals*. The
    list returned contains shallow copies of the input *individuals*.
    '''
    return sorted(individuals, key=lambda ind : ind.mFitness)[:n]


def tournSel(individuals, n, tournSize):
    '''Select *n* individuals from the input *individuals* using *n*
    tournaments of *tournSize* individuals. The list returned contains shallow
    copies of the input *individuals*. That means if an individual is selected
    twice, modifying one of the two occurences will modify the other.

    This function uses the :func:`choice` function from the python base
    :mod:`random` module.
    '''
    lChosenList = []
    for i in xrange(n):
        lChosenList.append(random.choice(individuals))
        for j in xrange(tournSize - 1):
            lAspirant = random.choice(individuals)
            if lAspirant.mFitness > lChosenList[i].mFitness:
                lChosenList[i] = lAspirant

    return lChosenList

######################################
# Migrations                         #
######################################

def ringMig(populations, n, selection, replacement=None, migrationArray=None,
            selKArgs=None, replKArgs=None):
    '''Perform a ring migration between the ``populations``. The migration first
    select *n* emmigrants from each population using the specified *selection*
    operator and then replace *n* individuals from the associated population in
    the *migrationArray* by themmigrants. If no *replacement*
    operator is specified, the immigrants will replace the emmigrants of the
    population, otherwise, the immigrants will replace the individuals selected
    by the *replacement* operator. The migration array if provided, shall
    contain each population's index once and only once. If no migration array
    is provided, it defaults to a serial ring migration (1-2-...-n-1). You may
    pass keyworded arguments to the two selection operators by giving a
    dictionary to *selKArgs* and *replKArds*.
    '''
    if migrationArray is None:
        migrationArray = [(i + 1) % len(populations) for i in xrange(len(populations))]
    else:
        for i in xrange(len(migrationArray)):
            try:
                migrationArray.index(i) 
            except: # TODO : Replace the bare except by the appropriate exception catching.
                raise ValueError, 'The migration array shall contain each population once and only once.'

    lImmigrants = [[]] * len(migrationArray)
    lEmigrants =  [[]] * len(migrationArray)
    if selKArgs is None:
        selKArgs = {}
    if replKArgs is None:
        replKArgs = {}

    for lFromDeme in xrange(len(migrationArray)):
        lEmigrants[lFromDeme].extend(selection(populations[lFromDeme], n=n,
                                     **selKArgs))
        if replacement is None:
            # If no replacement strategy is selected, replace those who migrate
            lImmigrants[lFromDeme] = lEmigrants[lFromDeme]
        else:
            # Else select those who will be replaced
            lImmigrants[lFromDeme].extend(replacement(populations[lFromDeme],
                                          n=n, **replKArgs))

    lMigBuf = lEmigrants[0]
    for lFromDeme, lToDeme in enumerate(migrationArray[1:]):
        lFromDeme += 1  # Enumerate starts at 0

        for i, lImmigrant in enumerate(lImmigrants[lToDeme]):
            lIndex = populations[lToDeme].index(lImmigrant)
            populations[lToDeme][lIndex] = lEmigrants[lFromDeme][i]

    lToDeme = migrationArray[0]
    for i, lImmigrant in enumerate(lImmigrants[lToDeme]):
        lIndex = populations[lToDeme].index(lImmigrant)
        populations[lToDeme][lIndex] = lMigBuf[i]

