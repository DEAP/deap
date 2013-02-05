.. _genprogtut:

Genetic Programming
===================

Genetic programming is a special field of evolutionary computation that aims
at building programs automatically to solve problem independently of their
domain. Although there exist vast diversity of representations used to evolve
programs, the most commonly used representation is the syntax tree which is
handled by DEAP in two forms, the loosely and strongly typed trees.

.. image:: /_images/gptree.png
   :align: center

For example, the above figure presents the program :math:`\max(x + 3 * y, x +
x)`. For this tree and further examples, the leaves of the tree, in green,
will be called terminals, while the internal nodes, in red, are called
primitves. The primitive set is the group containing all the possible
primitives and leaves. The terminals are divided in two subtypes, the
constants and the arguments. The constants remain the same for the entire
evolution while the arguments are the input of the program. For the last
presented tree, the arguments are the variables :math:`x` and :math:`y`, and
the constant is the number :math:`3`.


Loosely Typed Primitive Set
---------------------------
A loosely typed tree is one that does not force any type between the nodes.
More specifically, any primitive can take any type from the primitive set as
argument.

To define a loosely typed :class:`~deap.gp.PrimitiveSet` for the
previous tree use
::

	pset = PrimitiveSet("main", 2)
	pset.addPrimitive(max, 2)
	pset.addPrimitive(operator.add, 2)
	pset.addPrimitive(operator.mul, 2)
	pset.addTerminal(3)

The first line creates a primitive set called ``"main"`` taking 2 arguments as
input. The next three lines, add function as primitives. The first argument
tell what function to add and the second argument tells how many input they
take. The last line add a constant terminal. Currently the default name for
the arguments is ``"ARG0"`` and ``"ARG1"``. To change it to ``"x"`` and
``"y"`` simply call
::

	pset.renameArguments(ARG0="x")
	pset.renameArguments(ARG1="y")

In our case, all functons take two arguments. Having a 1 argument negation
function, for example, could be done with
::

	pset.addPrimitive(operator.neg, 1)

Our primitive set is now ready to generate some trees. The :mod:`~deap.gp`
module contains three generation functions for trees: :func:`~deap.gp.genFull`,
:func:`~deap.gp.genGrow`, and :func:`~deap.gp.genRamped`. They all take as
first argument the primitive set and return a valid list of primitives.
This list serves as argument to the :class:`~deap.gp.PrimitiveTree`
creator.
::
	
	expr = genFull(pset, min_=1, max_=3)
	tree = PrimitiveTree(expr)

The last code will produce a valid tree with depth randomly chosen between 2
and 4.

Strongly Typed Primitive Set
----------------------------
A strongly typed primitive set assigns types to every primitive and terminal
inputs and outputs. The output of a primitive must match the input of another
one if we want them to be connected. In this way a primitive can return a
boolean and this boolean would not be multipled with a float if the
multiplication operator operates only on floats. For example, the following code
::

	def if_then_else(input, output1, output2):
	    return output1 if input else output2

	pset = PrimitiveSetTyped("main", [bool, float], float)
	pset.addPrimitive(operator.xor, [bool, bool], bool)
	pset.addPrimitive(operator.mul, [float, float], float)
	pset.addPrimitive(if_then_else, [bool, float, float], float)
	pset.addTerminal(3.0, float)
	pset.addTerminal(1, bool)

	pset.renameArguments(ARG0="x")
	pset.renameArguments(ARG1="y")

can produce this tree.

.. image:: /_images/gptypedtree.png
   :align: center

In the last code sample, we first define an *if then else* function, that
returns the second argument if the first argument is true and the third one
otherwise. Then we define our :class:`~deap.gp.PrimitiveSetTyped` of name
``"main"``. Th second argument defines the input types of the program, here
``"x"`` is a :class:`bool` and ``"y"`` is a :class:`float`. The third argument
defines the output type of the program, a :class:`float`. Adding primitives to
this primitive set now requires us to set the input and output of the
primitives and terminal. For example, we define our if then else function as
taking a boolean as first input and floats as second and third input, it also
returns a float as output. We now understand that the multiplication primitive
can only have the terminal ``3.0``, the ``if_then_else`` function or the
``"y"`` as input, which are the only floats defined.

.. note::
   The generation of trees is made randomly. If any primitive as an input type
   that no terminal can provide, chances are that this primitive will be
   placed on the last layer of a tree resulting in the imposibility to
   complete the tree within the limit fixed by the generator. For example,
   when generating a full tree of depth 2, suppose ``"op"`` takes a boolean
   and a float, ``"and"`` takes 2 boolean and ``"neg"`` takes a float, no
   terminal is defined and the arguments ar booleans. The following situation
   will occur, no terminal can be placed to terminate the tree.
   
   |

   .. image:: /_images/gptypedinvtree.png
      :align: center

   In this situation you'll get an :class:`IndexError` with the message ``"The
   gp.generate function tried to add a terminal of type TYPE, but there is
   none available."``

Generation of Tree Individuals
------------------------------
The code presented in the last two sections produce valid trees. 
However, as in the :ref:`next-step` tutorial, these trees are not valid
individuals for evolution. One must combine the creator and the toolbox to
produce valid individuals. With the primitive set created earlier we will
create the :class:`Fitness` and the :class:`Individual` classes.
::

	creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
	creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin,
	               pset=pset)

Then we will register the generation function into a
:class:`~deap.base.Toolbox`.
::

	toolbox = base.Toolbox()
	toolbox.register("expr", gp.genFull, pset=pset, min_=1, max_=3)
	toolbox.register("individual", tools.initIterate, creator.Individual,
	                 toolbox.expr)

Calling :func:`toolbox.individual` will readily return an individual that is
a :class:`~deap.gp.PrimitiveTree`.

Ephemeral Constants
-------------------
An ephemeral constant is a terminal encapsulating a value that will be generated
from a given function a run time. Ephemeral constant are used to have terminals
that don't have all the same values. For example, to create an ephemeral constant
that takes its value in :math:`[-1, 1)` we use
::

	pset.addEphemeralConstant(lambda: random.uniform(-1, 1))

The ephemeral constant, when selected as a terminal for a tree, will contain a value
drawn from the interval independent of the last time it was drawn.
