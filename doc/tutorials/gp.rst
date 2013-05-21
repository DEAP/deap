.. _genprogtut:

Genetic Programming
===================

Genetic programming is a special field of evolutionary computation that aims
at building programs automatically to solve problems independently of their
domain. Although there exists diverse representations used to evolve
programs, the most common is the syntax tree.

.. image:: /_images/gptree.png
   :align: center

For example, the above figure presents the program :math:`\max(x + 3 * y, x +
x)`. For this tree and further examples, the leaves of the tree, in green,
are called terminals, while the internal nodes, in red, are called
primitves. The terminals are divided in two subtypes, the
constants and the arguments. The constants remain the same for the entire
evolution while the arguments are the program inputs. For the last
presented tree, the arguments are the variables :math:`x` and :math:`y`, and
the constant is the number :math:`3`.

In DEAP, user defined primitives and terminals are contained in a primitive
set. For now, there exists two kinds of primitive set, the loosely and the
strongly typed. 

Loosely Typed GP
----------------
Loosely typed GP does not enforce specific type between the nodes.
More specifically, primitives' arguments can be any primitives or terminals
present in the primitive set.

The following code define a loosely typed :class:`~deap.gp.PrimitiveSet` 
for the previous tree
::

	pset = PrimitiveSet("main", 2)
	pset.addPrimitive(max, 2)
	pset.addPrimitive(operator.add, 2)
	pset.addPrimitive(operator.mul, 2)
	pset.addTerminal(3)

The first line creates a primitive set. Its argument are the name of the
procedure it will generate ``"main"`` and its number of inputs, 2.
The next three lines add function as primitives. The first argument
is the function to add and the second argument the function arity_. 
The last line adds a constant terminal. Currently the default names for
the arguments are ``"ARG0"`` and ``"ARG1"``. To change it to ``"x"`` and
``"y"``, simply call
::

	pset.renameArguments(ARG0="x")
	pset.renameArguments(ARG1="y")

.. _arity: http://en.wikipedia.org/wiki/Arity

In this case, all functons take two arguments. Having a 1 argument negation
function, for example, could be done with
::

	pset.addPrimitive(operator.neg, 1)

Our primitive set is now ready to generate some trees. The :mod:`~deap.gp`
module contains three prefix expression generation functions 
:func:`~deap.gp.genFull`, :func:`~deap.gp.genGrow`, and 
:func:`~deap.gp.genRamped`. Their first argument is a primitive set 
and they return a valid prefix expression in the form of a list of primitives. 
The content of this list can be read by the :class:`~deap.gp.PrimitiveTree`
class to create a prefix tree.
::

	expr = genFull(pset, min_=1, max_=3)
	tree = PrimitiveTree(expr)

The last code produces a valid full tree with height randomly chosen 
between 1 and 3.

Strongly Typed GP
-----------------
In strongly typed GP, every primitive and terminal is assigned a specific
type. The output type of a primitive must match the input type of another
one for them to be connected. For example, a primitive can return a
boolean and this value is guaranteed to not be multipled with a float if the
multiplication operator operates only on floats.
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

In the last code sample, we first define an *if then else* function, that
returns the second argument if the first argument is true and the third one
otherwise. Then, we define our :class:`~deap.gp.PrimitiveSetTyped`. Again,
the procedure is named ``"main"``. The second argument defines the input types
of the program, here ``"x"`` is a :class:`bool` and ``"y"`` is a :class:`float`. 
The third argument defines the output type of the program, a :class:`float`. 
Adding primitives to this primitive now requires to set the input and 
output types of the primitives and terminal. For example, we define our 
``"if_then_else"`` function first argument as a boolean, the second and third
argument have to be floats. The function is defined as returning a float.
We now understand that the multiplication primitive can only have the 
terminal ``3.0``, the ``if_then_else`` function or the ``"y"`` as input, 
which are the only floats defined.

The preceding code can produce the tree on the left but not the one on
the right because the type restrictions.

.. image:: /_images/gptypedtrees.png
	:align: center

.. note::
   The generation of trees is done randomly while making sure type constraints
   are respected. If any primitive as an input type
   that no primitive and terminal can provide, chances are that this primitive will be
   picked and placed in the tree, resulting in the imposibility to
   complete the tree within the limit fixed by the generator. For example,
   when generating a full tree of height 2, suppose ``"op"`` takes a boolean
   and a float, ``"and"`` takes 2 boolean and ``"neg"`` takes a float, no
   terminal is defined and the arguments are booleans. The following situation
   will occur where no terminal can be placed to complete the tree.
   
   |

   .. image:: /_images/gptypederrtree.png
      :align: center

   In this case, DEAP raises an :class:`IndexError` with the message ``"The
   gp.generate function tried to add a terminal of type float, but there is
   none available."``

Ephemeral Constants
-------------------
An ephemeral constant is a terminal encapsulating a value that is generated
from a given function at run time. Ephemeral constants allow to have terminals
that don't have all the same values. For example, to create an ephemeral constant
that takes its value in :math:`[-1, 1)` we use
::

	pset.addEphemeralConstant(lambda: random.uniform(-1, 1))

The ephemeral constant value is determined when it is inserted in the tree and
never changes unless it is replaced by another ephemeral constant. Since it is
a terminal, ephemeral constant can also be typed
::

	pset.addEphemeralConstant(lambda: random.randint(-10, 10), int)

Generation of Tree Individuals
------------------------------
The code presented in the last two sections produce valid trees. 
However, as in the :ref:`next-step` tutorial, these trees are not yet valid
individuals for evolution. One must combine the creator and the toolbox to
produce valid individuals. We need to create the :class:`Fitness` and the
:class:`Individual` classes. To the :class:`Individual`, in addition to the
fitness we add a reference to the primitive set. This is used by some of the
gp operators to modify the individuals.
::

	creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
	creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin,
	               pset=pset)

We then register the generation functions into a :class:`~deap.base.Toolbox`.
::

	toolbox = base.Toolbox()
	toolbox.register("expr", gp.genFull, pset=pset, min_=1, max_=3)
	toolbox.register("individual", tools.initIterate, creator.Individual,
	                 toolbox.expr)

Calling :func:`toolbox.individual` readily returns an individual of type
:class:`~deap.gp.PrimitiveTree`.

Evaluation of Trees
-------------------

In DEAP, trees can be translated to readable Python code and compiled to
Python code object using functions provided by the :py:mod:`~deap.gp` 
module. The first function, :func:`~deap.gp.stringify` takes an expression
or a PrimitiveTree and translates it into readable Python code. For example,
the following lines generate a tree and output the code from the first example
primitive set
::

	>>> expr = genFull(pset, min_=1, max_=3)
	>>> tree = PrimitiveTree(expr)
	>>> stringify(tree)
	'mul(add(x, x), max(y, x))'
	
Now, this string represents the program we just generated, but it cannot
yet be executed. To do so, we have to compile the expression to
Python code object. Since this function has two inputs, we wish
to compile the code into a callable object. This is possible with 
:func:`~deap.gp.lambdify`. The term `lambdify` comes from the fact that
it returns a :keyword:`lambda` function corresponding to the code.
:func:`~deap.gp.lambdify` takes two arguments, the expression to compile and
the associated primitive set.
The following example compiles the preceding tree and evaluates the resulting
function for :math:`x=1` and :math:`y=2`.
::

	>>> function = lambdify(tree, pset)
	>>> function(1, 2)
	4

Finally, when the generated program has no input argument and terminals
are functions, the expression can be compiled to byte code using the
function :func:`~deap.gp.evaluate`. An example of this sort of problem
is the :ref:`artificial-ant`.

Tree Size Limit and Bloat Control
---------------------------------

Since DEAP uses the Python parser to compile the code represented
by the trees, it inherits from its limitations. The most commonly 
encountered restriction is the parsing stack limit. Python interpreter parser
stack limit is commonly fixed between 92 and 99. This means that
an expression can at most be composed of 91 succeeding primitives. In other
words, a tree can have a maximum depth of 91. 
When the limit is exceeded, Python raises the following error
::

	s_push: parser stack overflow 
	Traceback (most recent call last): 
	[...]
	MemoryError

Since this limit is hardcoded in the interpreter, there exists no
easy way to increase it. Furthermore, in GP this error commonly
stems from a phenomema known as bloat. That is, the produced individuals
have reached a point where they contain too much primitives to 
effectively solved the problem and the evolution stagnates. To counter
this, DEAP provides different functions that can effectively maintain 
the size and height of the trees under an acceptable limit. These
operators are listed in the GP section of :ref:`operators`.

How to Evolve Programs
----------------------

The different ways to evolve program trees are presented
through the :ref:`gpexamples` examples.

