import unittest

import numpy

from deap.base import Attribute, Fitness, Individual


class TestIndividualFitness(unittest.TestCase):
    def test_register_single_fitness(self):
        fitness = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness = fitness
        self.assertIn("my_fitness", ind._fitnesses)
        self.assertIs(ind._fitnesses["my_fitness"], fitness)

    def test_register_multi_fitnesses(self):
        fitness1 = Fitness(Fitness.MAXIMIZE)
        fitness2 = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness1 = fitness1
        ind.my_fitness2 = fitness2
        self.assertIn("my_fitness1", ind._fitnesses)
        self.assertIs(ind._fitnesses["my_fitness1"], fitness1)
        self.assertIn("my_fitness2", ind._fitnesses)
        self.assertIs(ind._fitnesses["my_fitness2"], fitness2)

    def test_get_single_fitness_no_key(self):
        fitness = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness = fitness
        self.assertIs(ind._getfitness(), fitness)

    def test_get_single_fitness_with_key(self):
        fitness = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness = fitness
        self.assertIs(ind._getfitness("my_fitness"), fitness)

    def test_get_multi_fitnesses_no_key_raises(self):
        fitness1 = Fitness(Fitness.MAXIMIZE)
        fitness2 = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness1 = fitness1
        ind.my_fitness2 = fitness2
        self.assertRaises(AttributeError, ind._getfitness)

    def test_get_multi_fitnesses_with_key(self):
        fitness1 = Fitness(Fitness.MAXIMIZE)
        fitness2 = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness1 = fitness1
        ind.my_fitness2 = fitness2
        self.assertIs(ind._getfitness("my_fitness1"), fitness1)
        self.assertIs(ind._getfitness("my_fitness2"), fitness2)

    def test_set_single_fitness_no_key(self):
        fitness = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness = fitness
        ind._setfitness(None, (3,))
        self.assertIs(ind._getfitness("my_fitness"), fitness)
        numpy.testing.assert_array_equal(fitness.value,
                                         numpy.asarray((3,),
                                                       dtype=numpy.float64))

    def test_set_single_fitness_with_key(self):
        fitness = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness = fitness
        ind._setfitness("my_fitness", (3,))
        self.assertIs(ind._getfitness("my_fitness"), fitness)
        numpy.testing.assert_array_equal(fitness.value,
                                         numpy.asarray((3,),
                                                       dtype=numpy.float64))

    def test_set_single_fitness_direct(self):
        fitness = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness = fitness
        ind.my_fitness = (3,)
        self.assertIs(ind._getfitness("my_fitness"), fitness)
        numpy.testing.assert_array_equal(fitness.value,
                                         numpy.asarray((3,),
                                                       dtype=numpy.float64))

    def test_set_single_fitness_single_value(self):
        fitness = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness = fitness
        ind._setfitness("my_fitness", 3)
        self.assertIs(ind._getfitness("my_fitness"), fitness)
        numpy.testing.assert_array_equal(fitness.value,
                                         numpy.asarray((3,),
                                                       dtype=numpy.float64))

    def test_set_multi_fitnesses_no_key_raises(self):
        fitness1 = Fitness(Fitness.MAXIMIZE)
        fitness2 = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness1 = fitness1
        ind.my_fitness2 = fitness2
        self.assertRaises(AttributeError, ind._setfitness, None, (3,))

    def test_set_multi_fitnesses_with_key(self):
        fitness1 = Fitness(Fitness.MAXIMIZE)
        fitness2 = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness1 = fitness1
        ind.my_fitness2 = fitness2
        ind._setfitness("my_fitness1", (3,))
        self.assertIs(ind._getfitness("my_fitness1"), fitness1)
        numpy.testing.assert_array_equal(fitness1.value,
                                         numpy.asarray((3,),
                                                       dtype=numpy.float64))
        ind._setfitness("my_fitness2", (5,))
        self.assertIs(ind._getfitness("my_fitness2"), fitness2)
        numpy.testing.assert_array_equal(fitness2.value,
                                         numpy.asarray((5,),
                                                       dtype=numpy.float64))

    def test_set_multi_fitnesses_direct(self):
        fitness1 = Fitness(Fitness.MAXIMIZE)
        fitness2 = Fitness(Fitness.MAXIMIZE)
        ind = Individual()
        ind.my_fitness1 = fitness1
        ind.my_fitness2 = fitness2
        ind.my_fitness1 = (3,)
        self.assertIs(ind._getfitness("my_fitness1"), fitness1)
        numpy.testing.assert_array_equal(fitness1.value,
                                         numpy.asarray((3,),
                                                       dtype=numpy.float64))
        ind.my_fitness2 = (5,)
        self.assertIs(ind._getfitness("my_fitness2"), fitness2)
        numpy.testing.assert_array_equal(fitness2.value,
                                         numpy.asarray((5,),
                                                       dtype=numpy.float64))

    def test_invalidate_single_fitness(self):
        fitness = Fitness(Fitness.MAXIMIZE, 3)
        ind = Individual()
        ind.my_fitness = fitness
        ind.invalidate_fitness()
        self.assertIs(ind.my_fitness, fitness)
        self.assertFalse(ind.my_fitness.valid)

    def test_invalidate_single_fitness_constraints(self):
        fitness = Fitness(Fitness.MAXIMIZE, 3, [True])
        ind = Individual()
        ind.my_fitness = fitness
        ind.invalidate_fitness()
        self.assertEqual(len(ind.my_fitness.violated_constraints), 0)

    def test_invalidate_multi_fitness(self):
        fitness1 = Fitness(Fitness.MAXIMIZE, 3)
        fitness2 = Fitness(Fitness.MAXIMIZE, 4)
        ind = Individual()
        ind.my_fitness1 = fitness1
        ind.my_fitness2 = fitness2
        ind.invalidate_fitness()
        self.assertIs(ind.my_fitness1, fitness1)
        self.assertIs(ind.my_fitness2, fitness2)
        self.assertFalse(ind.my_fitness1.valid)
        self.assertFalse(ind.my_fitness2.valid)


class TestIndividualAttribute(unittest.TestCase):
    def test_register_single_attribute(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        self.assertIn("my_attr", ind._attribute)
        self.assertIs(ind._attribute["my_attr"], attr)

    def test_register_multi_attributes(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertIn("my_attr1", ind._attribute)
        self.assertIs(ind._attribute["my_attr1"], attr1)
        self.assertIn("my_attr2", ind._attribute)
        self.assertIs(ind._attribute["my_attr2"], attr2)

    def test_get_single_attribute_no_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        self.assertIs(ind._getattribute(), attr)

    def test_get_single_attribute_with_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        self.assertIs(ind._getattribute("my_attr"), attr)

    def test_get_single_attribute_direct(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        self.assertIs(ind.my_attr, attr)

    def test_get_multi_attributes_no_key_raises(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertRaises(AttributeError, ind._getattribute)

    def test_get_multi_fitnesses_with_key(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertIs(ind._getattribute("my_attr1"), attr1)
        self.assertIs(ind._getattribute("my_attr2"), attr2)

    def test_get_multi_fitnesses_direct(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertIs(ind.my_attr1, attr1)
        self.assertIs(ind.my_attr2, attr2)

    def test_set_single_attribute_no_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        ind._setattribute(None, "abc")
        self.assertIs(ind._getattribute("my_attr"), attr)
        self.assertEqual(ind.my_attr.value, "abc")

    def test_set_single_attribute_with_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        ind._setattribute("my_attr", "abc")
        self.assertIs(ind._getattribute("my_attr"), attr)
        self.assertEqual(ind.my_attr.value, "abc")

    def test_set_single_attribute_direct(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        ind.my_attr = "abc"
        self.assertIs(ind._getattribute("my_attr"), attr)
        self.assertEqual(ind.my_attr.value, "abc")

    def test_set_multi_attributes_no_key_raises(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertRaises(AttributeError, ind._setattribute, None, "abc")

    def test_set_multi_attributes_with_key(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        ind._setattribute("my_attr1", "abc")
        self.assertIs(ind._getattribute("my_attr1"), attr1)
        self.assertEqual(attr1.value, "abc")
        ind._setattribute("my_attr2", "def")
        self.assertIs(ind._getattribute("my_attr2"), attr2)
        numpy.testing.assert_array_equal(attr2.value, "def")

    def test_set_multi_attributes_direct(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        ind.my_attr1 = "abc"
        self.assertIs(ind._getattribute("my_attr1"), attr1)
        self.assertEqual(attr1.value, "abc")
        ind.my_attr2 = "def"
        self.assertIs(ind._getattribute("my_attr2"), attr2)
        numpy.testing.assert_array_equal(attr2.value, "def")
