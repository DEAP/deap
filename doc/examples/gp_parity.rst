.. _parity:
    
===================
Even-Parity Problem
===================

Parity is one of the classical GP problems. The goal is to find a program
that produces the value of the Boolean even parity given n independent
Boolean inputs. Usually, 6 Boolean inputs are used (Parity-6), and the goal
is to match the good parity bit value for each of the :math:`2^6 = 64`
possible entries. The problem can be made harder by increasing the number of
inputs (in the DEAP implementation, this number can easily be tuned, as it is
fixed by a constant named PARITY_FANIN_M).

For more information about this problem, see :ref:`refPapersParity`.

Primitives set used
===================

Parity uses standard Boolean operators as primitives, available in the Python
operator module :
   
.. literalinclude:: /../examples/gp/parity.py
   :lines: 49-55
    
In addition to the *n* inputs, we add two constant terminals, one at 0, one
at 1.

.. note::
    As Python is a dynamic typed language, you can mix Boolean operators and
    integers without any issue.

    
Evaluation function
===================

In this implementation, the fitness of a Parity individual is simply the
number of successful cases. Thus, the fitness is maximized, and the maximum
value is 64 in the case of a 6 inputs problems.
   
.. literalinclude:: /../examples/gp/parity.py
   :pyobject: evalParity

`inputs` and `outputs` are two pre-generated lists, to speedup the
evaluation, mapping a given input vector to the good output bit. The Python
:func:`sum` function works on booleans (false is interpreted as 0 and true as
1), so the evaluation function boils down to sum the number of successful
tests : the higher this sum, the better the individual.

Conclusion
==========

The other parts of the program are mostly the same as the :ref:`Symbolic
Regression algorithm <symbreg>`.

The complete :example:`gp/parity`.

.. _refPapersParity:

Reference
=========

*John R. Koza, "Genetic Programming II: Automatic Discovery of Reusable
Programs", MIT Press, 1994, pages 157-199.*
