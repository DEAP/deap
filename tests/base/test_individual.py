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
        self.assertIn("my_attr", ind._attributes)
        self.assertTrue(hasattr(ind, "my_attr"))
        self.assertIs(ind._attributes["my_attr"], None)

    def test_register_single_attribute_multi_individual(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind1 = Individual()
        ind2 = Individual()
        ind1.my_attr1 = attr1
        ind2.my_attr2 = attr2
        self.assertIn("my_attr1", ind1._attributes)
        self.assertTrue(hasattr(ind1, "my_attr1"))
        self.assertNotIn("my_attr2", ind1._attributes)
        self.assertFalse(hasattr(ind1, "my_attr2"))

        self.assertNotIn("my_attr1", ind2._attributes)
        self.assertFalse(hasattr(ind2, "my_attr1"))
        self.assertIn("my_attr2", ind2._attributes)
        self.assertTrue(hasattr(ind2, "my_attr2"))

    def test_register_multi_attributes(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertIn("my_attr1", ind._attributes)
        self.assertIs(ind._attributes["my_attr1"], attr1)
        self.assertIn("my_attr2", ind._attributes)
        self.assertIs(ind._attributes["my_attr2"], attr2)

    def test_get_single_attribute_no_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        self.assertIsInstance(ind._getattribute(), Attribute)

    def test_get_single_attribute_with_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        self.assertIsInstance(ind._getattribute("my_attr"), Attribute)

    def test_get_single_attribute_direct(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        self.assertIsInstance(ind.my_attr, Attribute)

    def test_get_multi_attributes_no_key_raises(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertRaises(AttributeError, ind._getattribute)

    def test_get_multi_attributes_with_key(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertIsInstance(ind._getattribute("my_attr1"), Attribute)
        self.assertIsInstance(ind._getattribute("my_attr2"), Attribute)

    def test_get_multi_attributes_direct(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        self.assertIsInstance(ind.my_attr1, Attribute)
        self.assertIsInstance(ind.my_attr2, Attribute)

    def test_set_single_attribute_no_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        ind._setattribute(None, "abc")
        self.assertIsInstance(ind._getattribute("my_attr"), Attribute)
        self.assertEqual(ind.my_attr, "abc")

    def test_set_single_attribute_with_key(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        ind._setattribute("my_attr", "abc")
        self.assertIsInstance(ind._getattribute("my_attr"), Attribute)
        self.assertEqual(ind.my_attr, "abc")

    def test_set_single_attribute_direct(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        ind.my_attr = "abc"
        self.assertIsInstance(ind._getattribute("my_attr"), Attribute)
        self.assertEqual(ind.my_attr, "abc")

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
        self.assertIsInstance(ind._getattribute("my_attr1"), Attribute)
        self.assertEqual(attr1, "abc")
        ind._setattribute("my_attr2", "def")
        self.assertIsInstance(ind._getattribute("my_attr2"), Attribute)
        self.assertEqual(attr2, "def")

    def test_set_multi_attributes_direct(self):
        attr1 = Attribute()
        attr2 = Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr2
        ind.my_attr1 = "abc"
        self.assertIsInstance(ind._getattribute("my_attr1"), Attribute)
        self.assertEqual(attr1, "abc")
        ind.my_attr2 = "def"
        self.assertIsInstance(ind._getattribute("my_attr2"), Attribute)
        self.assertEqual(attr2, "def")

    def test_del_single_attribute(self):
        attr = Attribute()
        ind = Individual()
        ind.my_attr = attr
        del ind.my_attr
        self.assertNotIn("my_attr", ind._attributes)
        self.assertFalse(hasattr(ind, "my_attr"))

    def test_del_multi_attributes(self):
        attr1= Attribute()
        attr2= Attribute()
        ind = Individual()
        ind.my_attr1 = attr1
        ind.my_attr2 = attr1
        del ind.my_attr1
        del ind.my_attr2
        self.assertNotIn("my_attr1", ind._attributes)
        self.assertFalse(hasattr(ind, "my_attr1"))
        self.assertNotIn("my_attr2", ind._attributes)
        self.assertFalse(hasattr(ind, "my_attr2"))

    def test_del_single_attribute_multi_individuals(self):
        attr = Attribute()
        ind1 = Individual()
        ind2 = Individual()
        ind1.my_attr = attr
        ind2.my_attr = attr
        del ind1.my_attr
        self.assertNotIn("my_attr", ind1._attributes)
        self.assertFalse(hasattr(ind1, "my_attr"))
        self.assertIn("my_attr", ind2._attributes)
        self.assertTrue(hasattr(ind2, "my_attr"))


class TestIndividualHeritance(unittest.TestCase):
    class TestIndividual(Individual):
        def __init__(self, initval=None):
            super().__init__()
            self.fitness = Fitness(Fitness.MINIMIZE)
            self.attr = Attribute(initval)

    class TestIndividualNoSuperInit(Individual):
        def __init__(self, initval=None):
            self.fitness = Fitness(Fitness.MINIMIZE)
            self.attr = Attribute(initval)

    class TestIndividualNoSuperInitAttrFirst(Individual):
        def __init__(self, initval=None):
            self.attr = Attribute(initval)
            self.fitness = Fitness(Fitness.MINIMIZE)

    def test_subclass_has_all_attr(self):
        ind = TestIndividualHeritance.TestIndividual()
        self.assertTrue(hasattr(ind, "_fitnesses"))
        self.assertTrue(hasattr(ind, "_attributes"))
        self.assertTrue(hasattr(ind, "fitness"))
        self.assertTrue(hasattr(ind, "attr"))

    def test_subclass_no_super_init_raises(self):
        with self.assertRaisesRegex(AttributeError, r"cannot assign \w+ before Individual\.__init__\(\) call"):
            TestIndividualHeritance.TestIndividualNoSuperInit()

    def test_subclass_no_super_init_raises_attr(self):
        with self.assertRaisesRegex(AttributeError, r"cannot assign \w+ before Individual\.__init__\(\) call"):
            TestIndividualHeritance.TestIndividualNoSuperInitAttrFirst()
