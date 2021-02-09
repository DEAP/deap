import unittest

import numpy

from deap.base import Attribute


class TestBaseAttribute(unittest.TestCase):
    def test_get_value(self):
        a = Attribute(3)
        self.assertEqual(a._getvalue(), 3)

    def test_set_value(self):
        a = Attribute()
        a._setvalue(3)
        self.assertEqual(a.value, 3)

    def test_del_value(self):
        a = Attribute(3)
        a._delvalue()
        self.assertEqual(a.value, None)

    def test_str(self):
        value = 3
        a = Attribute(value)
        str_a = str(a)
        self.assertEqual(str_a, str(value))
