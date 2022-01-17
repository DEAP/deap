import unittest

import numpy

from deap.base import Attribute


class TestBaseAttribute(unittest.TestCase):
    def test_init_value_none(self):
        a = Attribute()
        self.assertEqual(a, None)

    def test_init_value(self):
        init_val = 3
        a = Attribute(init_val)
        self.assertEqual(a, init_val)

    def test_unwrap(self):
        init_val = {"a": 3}
        a = Attribute(init_val)
        expected = a.unwrap()
        self.assertIs(expected, init_val)


# class TestNumpyAttribute(unittest.TestCase):
    # def test_add_value(self):
    #     a = Attribute(numpy.array([1, 2, 3]))
    #     a += 3
    #     numpy.testing.assert_equal(a, [4, 5, 6])

    # def test_dot_attributes(self):
    #     list_ = [1, 2, 3]
    #     # array = numpy.array(list_)
    #     attr = Attribute(list_)

    #     expected = numpy.dot(list_, list_)
    #     result = numpy.dot(attr, attr)

    #     numpy.testing.assert_equal(expected, result)

    # def test_array_attributes(self):
    #     list_ = [1, 2, 3]
    #     attr = Attribute(list_)

    #     expected = numpy.array([list_, list_])
    #     result = numpy.array([attr, attr])

    #     numpy.testing.assert_equal(expected, result)
