#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

from nose import with_setup
from unittest import skipIf

import array

try:
    import numpy
except ImportError:
    numpy = False

from deap import creator

CNAME = "CLASS_NAME"

def teardown_func():
    creator.__dict__.pop(CNAME)

@with_setup(None, teardown_func)
def test_create():
    creator.create(CNAME, list)
    l = creator.__dict__[CNAME]([1,2,3,4])

    assert l == [1,2,3,4], "%s, expected %s" % (l, [1,2,3,4])

@with_setup(None, teardown_func)
def test_attribute():
    creator.create(CNAME, list, a=1)
    l = creator.__dict__[CNAME]([1,2,3,4])

    assert l.a == 1, "%s, expected %i" % (l.a, 1)

@with_setup(None, teardown_func)
def test_array():
    creator.create(CNAME, array.array, typecode="i")
    a = creator.__dict__[CNAME]([1,2,3,4])
    b = creator.__dict__[CNAME]([5,6,7,8])

    a[1:3], b[1:3] = b[1:3], a[1:3]
    ta = array.array("i", [1,6,7,4])
    tb = array.array("i", [5,2,3,8])
    assert a == ta, "%s, expected %s" % (a, ta)
    assert b == tb, "%s, expected %s" % (b, tb)

@skipIf(not numpy, "Cannot import Numpy numerical library")
@with_setup(None, teardown_func)
def test_numpy_nocopy():
    creator.create(CNAME, numpy.ndarray)
    a = creator.__dict__[CNAME]([1,2,3,4])
    b = creator.__dict__[CNAME]([5,6,7,8])

    a[1:3], b[1:3] = b[1:3], a[1:3]
    ta = numpy.array([1,6,7,4])
    tb = numpy.array([5,6,7,8])
    assert all(a == ta), "%s, expected %s" % (a, ta)
    assert all(b == tb), "%s, expected %s" % (b, tb)

@skipIf(not numpy, "Cannot import Numpy numerical library")
@with_setup(None, teardown_func)
def test_numpy_copy():
    creator.create(CNAME, numpy.ndarray)
    a = creator.__dict__[CNAME]([1,2,3,4])
    b = creator.__dict__[CNAME]([5,6,7,8])

    a[1:3], b[1:3] = b[1:3].copy(), a[1:3].copy()
    ta = numpy.array([1,6,7,4])
    tb = numpy.array([5,2,3,8])
    assert all(a == ta), "%s, expected %s" % (a, ta)
    assert all(b == tb), "%s, expected %s" % (b, tb)
