import sys
import unittest

from deap.benchmarks import binary


class TestBin2Float(unittest.TestCase):
    """Test object for unittest of deap/benchmarks."""

    def setUp(self):
        self.b2f = binary.bin2float(0, 1023, 10)(lambda x: x)

    def test_zero(self):
        zero = [0] * 10
        res = self.b2f(zero)
        self.assertSequenceEqual(res, [0])

    def test_full(self):
        full = [1] * 10
        res = self.b2f(full)
        self.assertSequenceEqual(res, [1023])

    def test_two(self):
        two = [0] * 8 + [1, 0]
        res = self.b2f(two)
        self.assertSequenceEqual(res, [2])

    def test_one_two(self):
        one = [0] * 9 + [1]
        two = [0] * 8 + [1, 0]
        one_two = one + two
        res = self.b2f(one_two)
        self.assertSequenceEqual(res, [1, 2])

    @unittest.skipUnless(sys.version_info < (3, ), "Python 2")
    def test_wrong_size_raises_py2(self):
        wrong = [0, 1, 0, 1, 0, 1, 0, 1, 1]
        with self.assertRaises(TypeError):
            self.b2f(wrong)

    @unittest.skipUnless(sys.version_info >= (3, ), "Python 3+")
    def test_wrong_size_no_value_py3(self):
        wrong = [0, 1, 0, 1, 0, 1, 0, 1, 1]
        res = self.b2f(wrong)
        self.assertEqual(len(res), 0)
