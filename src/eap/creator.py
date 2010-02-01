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

from ConfigParser import RawConfigParser
from functools import partial

class Creator(object):
    '''The creator is an abstract factory that produce objects by calling their
    constructor with that arguments defined in the :meth:`define` method.
    '''
    def define(self, methodName, constructor, *args, **kargs):
        '''Register a method to be called with :meth:`methodName()`, *args* and
        *kargs* will be passed as argument to the method. Supplying new
        keyworded arguments to the calee will override the predifined *kargs*.
        For example, using ::

            >>> def foo(a, b=1):
            ...     print a, b
            ...
            >>> creator = Creator()
            >>> creator.define('bar', foo, a=1, b=2)

        the following are possible. ::

            >>> creator.bar()
            1 2
            >>> creator.bar(a=2, b=4)
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

    def undefine(self, methodName):
        '''Unregister the method named *methodName*.'''
        delattr(self, methodName)

    def dump(self, fileName):
        '''Dump the creator to a file named *fileName*.'''
        lConfig = RawConfigParser()
        for lAttr in self.__dict__:
            lConfig.add_section(lAttr)
            lClassAndPath = self.__dict__[lAttr].func.__module__ + \
                            '.' + self.__dict__[lAttr].func.__name__
            lConfig.set(lAttr, 'type', lClassAndPath)

            for lOption in self.__dict__[lAttr].keywords:
                lConfig.set(lAttr, lOption, \
                            self.__dict__[lAttr].keywords[lOption])

        lFile = open(fileName, 'w')
        lConfig.write(lFile)
        lFile.close()

    def load(self, fileName):
        '''Configure the creator from a configuration file named *fileName*.
        Methods registered with same name as the one in the configuration file
        will be overriden.
        '''
        lConfig = RawConfigParser()
        lConfig.read(fileName)
        for lSection in lConfig.sections():
            kargs = dict()
            for lOption in lConfig.options(lSection):
                lValue = None
                try:
                    lValue = eval(lConfig.get(lSection, lOption))
                except NameError:
                    lValue = lConfig.get(lSection, lOption)
                kargs[lOption] = lValue
            lImportString = kargs['type'].split('.')
            lModule = __import__(lImportString[0])
            kargs.pop('type')
            self.register(lSection, getattr(lModule, lImportString[1]),
                          *args, **kargs)


#creator_instance = Creator_()
#
#
#def Creator():
#    '''Creator singleton accessor.'''
#    return creator_instance
