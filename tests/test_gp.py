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
import re
import operator
from deap import gp

try:
    import sympy as sp
except ImportError:
    sp = None


class TestGP(unittest.TestCase):
    def setUp(self):
        pass

    @unittest.skipUnless(sp, 'Sympy is not installed')
    def test_gp_expression_func(self):
        pset = gp.PrimitiveSet("MAIN", arity=5, prefix='x')
        pset.addPrimitive(operator.add, 2)
        pset.addPrimitive(operator.sub, 2)
        pset.addPrimitive(operator.mul, 2)
        pset.addPrimitive(operator.truediv, 2)
        pset.addPrimitive(operator.neg, 1)

        tree = gp.PrimitiveTree.from_string("add(neg(x0), mul(x1, truediv(x2, sub(x3, x4))))", pset=pset)
        func_sym_mapping = {
            'add': operator.add,
            'sub': operator.sub,
            'mul': operator.mul,
            'neg': operator.neg
        }
        expr_string = tree.expression(func_sym_mapping)
        expr_string = re.sub(r'\s', '', expr_string)
        self.assertEqual(expr_string, '-x0+x1*truediv(x2,x3-x4)')

        func_sym_mapping['truediv'] = operator.truediv

        expr_string = tree.expression(func_sym_mapping)
        expr_string = re.sub(r'\s', '', expr_string)
        self.assertEqual(expr_string, '-x0+x1*x2/(x3-x4)')

    @unittest.skipUnless(sp, 'Sympy is not installed')
    def test_gp_expression_symbol(self):
        pset = gp.PrimitiveSet("MAIN", arity=2, prefix='x')
        pset.addPrimitive(operator.add, 2)
        pset.addPrimitive(operator.pow, 2)
        pset.addPrimitive(sp.sqrt, 1)
        pset.addPrimitive(min, 2)

        tree = gp.PrimitiveTree.from_string("min(sqrt(pow(x0, 2)), min(x1, add(x0, x0)))", pset=pset)
        func_sym_mapping = {
            'add': operator.add,
            'pow': operator.pow,
            'sqrt': sp.sqrt,
            'min': sp.Min
        }

        terminal_sym_mapping = {
            'x0': sp.Symbol('x0', real=True)
        }
        expr_string = tree.expression(func_sym_mapping, **terminal_sym_mapping)
        expr_string = re.sub(r'\s', '', expr_string)
        self.assertEqual(expr_string, 'Min(2*x0,x1,Abs(x0))')

        terminal_sym_mapping = {
            'x0': sp.Symbol('x0', positive=True)
        }
        expr_string = tree.expression(func_sym_mapping, **terminal_sym_mapping)
        expr_string = re.sub(r'\s', '', expr_string)
        self.assertEqual(expr_string, 'Min(x0,x1)')

        terminal_sym_mapping = {
            'x0': sp.Symbol('x0', negative=True),
            'x1': sp.Symbol('x0', positive=True)
        }
        expr_string = tree.expression(func_sym_mapping, **terminal_sym_mapping)
        expr_string = re.sub(r'\s', '', expr_string)
        self.assertEqual(expr_string, '2*x0')


