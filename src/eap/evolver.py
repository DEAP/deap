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

'''The :mod:`creator` module is an helper module in order to simplify the
object creation. Its one and only purpose is to register some function that can
be called as generator in populations' and individuals' *generator* argument.
The creator is responsible of intanciating the objects needed by the algorithms.
'''

from functools import partial
import random

class Evolver(object):
    '''The creator is an abstract factory that produce objects by calling their
    constructor with the arguments defined in the :meth:`define` method.
    '''
    def register(self, methodName, constructor, *args, **kargs):
        '''Register a method to be called with :meth:`methodName()`, *args* and
        *kargs* will be passed as argument to the method. Supplying new
        keyworded arguments to the calee will override the predifined *kargs*.
        For example, using ::

            >>> def foo(a, b=1):
            ...     print a, b
            ...
            >>> evolver.define('bar', foo, a=1, b=2)

        the following are possible. ::

            >>> evolver.bar()
            1 2
            >>> evolver.bar(a=2, b=4)
            2 4

        But if no keyworded arguments are used, then is will be imposible to
        change the argument as the new arguments will be appended at the end
        of the argument list. ::

            >>> creator.define('baz', foo, 1, 2)
            >>> creator.baz(2, b=4)

        This will raise a TypeError for too much arguments. Although, this
        will work fine ::

            >>> creator.define('baz', foo, 1)
            >>> creator.baz(b=4)
            1 4

        .. note::
           The common use of the creator is to define all only keyworded
           arguments for clarity and simplicity.
        '''
        setattr(self, methodName, partial(constructor, *args, **kargs))

    def unregister(self, methodName):
        '''Unregister the method named *methodName*.'''
        delattr(self, methodName)


#_inst = Evolver()
#register = _inst.register
#unregister = _inst.unregister

def simpleGA(evolver, population, cxPb, mutPb, nGen):
    # Begin the evolution
    for g in range(nGen):
        print 'Generation', g

        population[:] = evolver.select(population, n=len(population))

        # Apply crossover and mutation
        for i in xrange(1, len(population), 2):
            if random.random() < cxPb:
                population[i - 1], population[i] = evolver.crossover(population[i - 1], population[i])
        for i in xrange(len(population)):
            if random.random() < mutPb:
                population[i] = evolver.mutate(population[i])

        # Evaluate the population
        map(evolver.evaluate, population)

        # Gather all the fitnesses in one list and print the stats
        lFitnesses = [lInd.mFitness[0] for lInd in population]
        print '\tMin Fitness :', min(lFitnesses)
        print '\tMax Fitness :', max(lFitnesses)
        print '\tMean Fitness :', sum(lFitnesses)/len(lFitnesses)

    print 'End of evolution'
