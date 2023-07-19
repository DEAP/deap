import unittest
from unittest import mock

from deap.tools.mutation import mutInversion


class MutationTest(unittest.TestCase):

    def test_mutInverstion_size_zero_chromosome_returns_unchanged_chromosome_in_tuple(self):
        chromosome = []
        expected = []
        self.assertEqual((expected,), mutInversion(chromosome))

    def test_mutInversion_size_one_chromosome_returns_unchanged_chromosome_in_tuple(self):
        chromosome = ["a"]
        expected = ["a"]
        self.assertEqual((expected,), mutInversion(chromosome))

    @mock.patch("random.randrange")
    def test_mutInversion_same_random_indices_returns_unchanged_chromosome_in_tuple(self, mock_randrange):
        mock_randrange.side_effect = [2, 2]
        chromosome = ["a", "b", "c", "d", "e"]
        expected = ["a", "b", "c", "d", "e"]
        self.assertEqual((expected,), mutInversion(chromosome))

    @mock.patch("random.randrange")
    def test_mutInversion_difference_of_one_random_indices_returns_unchanged_chromosome_in_tuple(self, mock_randrange):
        mock_randrange.side_effect = [2, 3]
        chromosome = ["a", "b", "c", "d", "e"]
        expected = ["a", "b", "c", "d", "e"]
        self.assertEqual((expected,), mutInversion(chromosome))

    @mock.patch("random.randrange")
    def test_mutInversion_full_length_random_indices_returns_reversed_chromosome_in_tuple(self, mock_randrange):
        mock_randrange.side_effect = [0, 5]
        chromosome = ["a", "b", "c", "d", "e"]
        expected = ["e", "d", "c", "b", "a"]
        self.assertEqual((expected,), mutInversion(chromosome))

    @mock.patch("random.randrange")
    def test_mutInversion_general_case_returns_correctly_mutated_chromosome_in_tuple(self, mock_randrange):
        mock_randrange.side_effect = [1, 4]
        chromosome = ["a", "b", "c", "d", "e"]
        expected = ["a", "d", "c", "b", "e"]
        self.assertEqual((expected,), mutInversion(chromosome))
