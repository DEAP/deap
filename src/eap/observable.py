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

'''The observable module provide an internal mechanism to observe changes in
the elements of the evolutionary algorithm. It is used by the statistic
generators to observe the populations and individuals.
'''

import stats

class Observable(object):
    '''The observer/observable pattern is used for statistics management. The
    behavior of this pattern is slightly modified has a call to :meth:`emit`
    does not only activates all the observers but push the statistics that are
    returned to a statistics container.
    '''
    def __init__(self):
        self.mSuscribers = {}

    def emit(self, output=stats):
        '''Emit the signal that this object has changed, each suscriber then
        call the :meth:`send` method with argument *self*. The results are
        pushed in the *output* object with method :meth:`~eap.stats.pushStats`.
        The default value for *output* is the hidden instance of the module
        :mod:`stats`.
        '''
        for lSuscriber in self.mSuscribers.iteritems():
            output.pushStats(lSuscriber[0], lSuscriber[1].send(self))

    def suscribe(self, suscriberName, suscriberObject):
        '''Suscribe an initialized generator function to this observable. The
        generator function is passed via the *suscriberObject* argument, while
        the *suscriberName* is used in the statistics container to access the
        statistics.
        '''
        self.mSuscribers[suscriberName] = suscriberObject
        self.mSuscribers[suscriberName].next()

    def unsuscribe(self, suscriberName):
        '''Unsuscribe the function registered  with name *suscriberName*.'''
        del self.mSuscribers[suscriberName]

