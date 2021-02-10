import unittest

from deap.base import Toolbox


class TestToolbox(unittest.TestCase):
    has_attr_default_message = "{obj} misses attribute {attrname}"

    def assertHasAttr(self, obj, attrname, message=None):
        if message is None:
            message = self.has_attr_default_message.format(
                obj=obj,
                attrname=attrname
            )

        self.assertTrue(
            hasattr(obj, attrname),
            msg=message
        )

    def test_has_map(self):
        tb = Toolbox()
        self.assertHasAttr(tb, "map")

    def test_register_has_attr(self):
        def func(x):
            return x

        tb = Toolbox()
        tb.register("abc", func)
        self.assertHasAttr(tb, "abc")

    def test_register_attr_has_new_name(self):
        def func(x):
            return x

        tb = Toolbox()
        tb.register("abc", func)
        self.assertEqual(tb.abc.__name__, "abc")

    def test_register_attr_has_docstring(self):
        def func(x):
            "docstring"
            return x

        tb = Toolbox()
        tb.register("abc", func)
        self.assertEqual(tb.abc.__doc__, "docstring")
