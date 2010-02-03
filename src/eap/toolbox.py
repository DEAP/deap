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

'''The evolution toolbox is intended to contain the operators that you need in
your evolutionary algorithms. It is always possible to use directly the
operators from the module :mod:`eap.operators` but the toolbox does also contain
the default values of the different parameters for each method. More over, it
makes your algorithms easier to understand and modify, since once an oprerator
is set, it can be reused with a simple keyword that conatins all its arguments.
Plus, every keyword or argument can be overriden at all time.
'''

from functools import partial

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


#class SimpleGAToolbox(EvolutionToolbox):
#    '''An evolutionary toolbox intended for simple genetic algorithms. Is is
#    initialized with :meth:`mate` that apply a two points crossover with method
#    :meth:`eap.operators.twoPointsCx`, :meth:`mutate` that apply a gaussian
#    mutation with method :meth:`eap.operators.gaussMut` and :meth:`select` that
#    select individuals using a tournament with method
#    :meth:`eap.operators.tournSel`.
#    '''
#
#    def __init__(self):
#        self.register('mate', operators.twoPointsCx)
#        self.register('mutate', operators.gaussMut)
#        self.register('select', operators.tournSel)
#
#
#class IndicesGAToolbox(EvolutionToolbox):
#    '''An evolutionary toolbox intended for simple genetic algorithms. Is is
#    initialized with :meth:`mate` that apply a partialy matched crossover with
#    method :meth:`eap.operators.pmxCx`, :meth:`mutate` that apply a shuffle
#    indices mutation with method :meth:`eap.operators.shuffleIndxMut` and
#    :meth:`select` that select individuals using a tournament with method
#    :meth:`eap.operators.tournSel`.
#
#    .. versionadded:: 0.2.0a
#       The toolbox for indice representation has been added for convenience.
#    '''
#
#    def __init__(self):
#        self.register('mate', operators.pmxCx)
#        self.register('mutate', operators.shuffleIndxMut)
#        self.register('select', operators.tournSel)
