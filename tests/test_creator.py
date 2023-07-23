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

import unittest

import array

try:
    import numpy
except ImportError:
    numpy = False

from deap import creator

CNAME = "CLASS_NAME"


class TestCreator(unittest.TestCase):
    def tearDown(self):
        creator.__dict__.pop(CNAME)

    def test_create(self):
        creator.create(CNAME, list)
        result = creator.__dict__[CNAME]([1, 2, 3, 4])
        self.assertSequenceEqual(result, [1, 2, 3, 4])

    def test_attribute(self):
        creator.create(CNAME, list, a=1)
        result = creator.__dict__[CNAME]([1, 2, 3, 4])
        self.assertEqual(result.a, 1)

    def test_array(self):
        creator.create(CNAME, array.array, typecode="i")
        a = creator.__dict__[CNAME]([1, 2, 3, 4])
        b = creator.__dict__[CNAME]([5, 6, 7, 8])

        a[1:3], b[1:3] = b[1:3], a[1:3]
        ta = array.array("i", [1, 6, 7, 4])
        tb = array.array("i", [5, 2, 3, 8])
        self.assertSequenceEqual(a, ta)
        self.assertSequenceEqual(b, tb)

    @unittest.skipIf(not numpy, "Cannot import Numpy numerical library")
    def test_numpy_nocopy(self):
        creator.create(CNAME, numpy.ndarray)
        a = creator.__dict__[CNAME]([1, 2, 3, 4])
        b = creator.__dict__[CNAME]([5, 6, 7, 8])

        a[1:3], b[1:3] = b[1:3], a[1:3]
        ta = numpy.array([1, 6, 7, 4])
        tb = numpy.array([5, 6, 7, 8])
        numpy.testing.assert_array_equal(a, ta)
        numpy.testing.assert_array_equal(b, tb)

    @unittest.skipIf(not numpy, "Cannot import Numpy numerical library")
    def test_numpy_copy(self):
        creator.create(CNAME, numpy.ndarray)
        a = creator.__dict__[CNAME]([1, 2, 3, 4])
        b = creator.__dict__[CNAME]([5, 6, 7, 8])

        a[1:3], b[1:3] = b[1:3].copy(), a[1:3].copy()
        ta = numpy.array([1, 6, 7, 4])
        tb = numpy.array([5, 2, 3, 8])
        numpy.testing.assert_array_equal(a, ta)
        numpy.testing.assert_array_equal(b, tb)
