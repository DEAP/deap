import unittest
import random

from deap import gp


class Shape(object):
    """Base class standing in for any abstract return type."""


class Circle(Shape):
    pass


class Square(Shape):
    pass


def make_circle(radius):
    return Circle()


def make_square(side):
    return Square()


def full_height(height, depth):
    return depth >= height


class TestPrimitiveSetTypedReturnType(unittest.TestCase):
    """The primitive set's declared return type must be usable even when it is
    a base class that no terminal or primitive returns exactly.

    ``PrimitiveSetTyped._add`` registers the return and argument types of every
    node, but the primitive set's own ``ret`` type was never registered. When
    ``ret`` is a base class and all nodes return strict subclasses, no entry was
    ever created for it, so ``gp.generate`` selected from an empty list.
    """

    def test_base_return_type_with_subclass_primitives(self):
        pset = gp.PrimitiveSetTyped("MAIN", [float], Shape)
        pset.addPrimitive(make_circle, [float], Circle)
        pset.addPrimitive(make_square, [float], Square)

        # The declared return type must be a registered key, otherwise
        # generate() cannot pick a root node for it.
        self.assertIn(Shape, pset.primitives)
        self.assertEqual(len(pset.primitives[Shape]), 2)

        random.seed(0)
        # min_ == max_ == 1 puts a primitive at the root (Shape) and the
        # built-in ARG0 terminal at the leaf (float), so generation only needs
        # primitives[Shape] to resolve.
        expr = gp.generate(pset, min_=1, max_=1, condition=full_height)
        tree = gp.PrimitiveTree(expr)

        self.assertTrue(issubclass(tree.root.ret, Shape))
        self.assertIn(tree.root.ret, (Circle, Square))

        self.assertIsInstance(gp.compile(tree, pset)(2.0), Shape)

    def test_base_return_type_with_subclass_terminals(self):
        pset = gp.PrimitiveSetTyped("MAIN", [float], Shape)
        pset.addTerminal(Circle(), Circle, name="circle")
        pset.addTerminal(Square(), Square, name="square")

        self.assertIn(Shape, pset.terminals)
        self.assertEqual(len(pset.terminals[Shape]), 2)

        random.seed(0)
        # A zero-height tree stops at the root, so terminals[Shape] is the only
        # lookup required.
        expr = gp.generate(pset, min_=0, max_=0, condition=full_height)
        tree = gp.PrimitiveTree(expr)

        self.assertIn(tree.root.ret, (Circle, Square))
        self.assertIsInstance(gp.compile(tree, pset)(2.0), Shape)

    def test_exact_return_type_still_generates(self):
        # Guards against regressing the common case where the primitive set
        # returns exactly the type its nodes return.
        pset = gp.PrimitiveSetTyped("MAIN", [float], float)
        pset.addTerminal(1.0, float)
        pset.addPrimitive(make_circle, [float], Circle)
        pset.addPrimitive(make_square, [float], Square)

        self.assertIn(float, pset.primitives)
        self.assertEqual(pset.primitives[float], [])

        random.seed(0)
        expr = gp.generate(pset, min_=0, max_=0, condition=full_height)

        self.assertIs(gp.PrimitiveTree(expr).root.ret, float)

    def test_base_argument_type_still_resolves(self):
        # A base class used only as a primitive argument type already resolved
        # through _add; confirm that behaviour is unchanged.
        pset = gp.PrimitiveSetTyped("MAIN", [Shape], Circle)
        pset.addTerminal(Circle(), Circle, name="circle")
        pset.addTerminal(Square(), Square, name="square")
        pset.addPrimitive(make_circle, [Shape], Circle)

        # ARG0, the built-in argument terminal of type Shape, plus the two
        # terminals that return strict subclasses of Shape.
        self.assertEqual(len(pset.terminals[Shape]), 3)

        random.seed(0)
        expr = gp.generate(pset, min_=1, max_=1, condition=full_height)

        self.assertIs(gp.PrimitiveTree(expr).root.ret, Circle)
