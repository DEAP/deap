Speed up the evolution
=========================

Although pure performance is not one of the most important objectives of DEAP,
it may be good to know some ways to speed things up. This section will present
various ways to improve performance without loosing too much of the DEAP ease
of use. To show an approximation of the speedup you can achieve with each
technique, an example is provided (despite the fact that every problem is
different and will obviously produce different speedups).

.. note::
   The benchmarks were run on a Linux workstation (Core i7 920, 8 GB), with a
   standard Python distribution (2.7) and DEAP 0.8.

The comparison problem : Sorting Networks
-----------------------------------------

From `Wikipedia <http://en.wikipedia.org/wiki/Sorting_networks>`_ : *A sorting
network is an abstract mathematical model of a network of wires and comparator
modules that is used to sort a sequence of numbers. Each comparator connects
two wires and sort the values by outputting the smaller value to one wire, and
a larger value to the other.*

Genetic algorithms are an interesting way to generate arbitrary sorting
networks, as the fitness function of a network can easily be defined.
Moreover, this problem is a good benchmark for evolutionnary framework : its
complexity (and therefore the resources needed) can be tuned by changing the
number of inputs. A 6-inputs problems is fairly simple and will be solved in a
few seconds, while a 20-inputs one will take several minutes for each
*generation*.

For this benchmark, we used an input size of 12, with 500 individuals which
are allowed to evolve for 20 generations. Times reported are the total
duration of the program, including initialization.

Normal run
----------

*Time taken : 147 seconds (Reference time)*

With no optimizations at all, the level of performance reached is not
impressive, yet sufficient for most users, especially for prototyping.

Using PyPy
----------

*Time taken : 36 seconds (4.1x faster)*

PyPy (here in version 1.7) is an alternative Python interpreter which includes
a Just-In-Time (JIT) compiler to greatly improve performances, especially when
facing several rehearsals of the same loop or function. No change at all is
needed in the program, and except for external C modules and advanced
properties, PyPy is fully compliant with the Python 2.7 API.

To run your evolution under PyPy, simply `download it <http://pypy.org/>`_,
install it, and launch :
::
    
    pypy your_program.py

Considering the ease of use, the speedup reached is substantial, and therefore
makes a good first possibility to accelerate the execution.


Using the C++ version of the NSGA II algorithm
----------------------------------------------

*Time taken : 121 seconds (1.2x faster)*

Starting with DEAP 0.8, a module named *cTools* is provided. This module
includes a subset of the deap.tools module, but is implemented in C to improve
performances. Only the bottleneck functions (in term of computational effort)
are provided in *cTools*, with the exact same API and behaviour as their
pure-Python implementation. The NSGA-II selection algorithm is one of them,
and can be used here to improve performances, by only adding one line (the
module inclusion) and changing a second (the registration of the selection
algorithm).

    
.. literalinclude:: /code/tutorials/part_4/4_4_Using_Cpp_NSGA.py
   :lines: 22-22

.. literalinclude:: /code/tutorials/part_4/4_4_Using_Cpp_NSGA.py
   :lines: 69-69

As one can see, the speedup reached is somewhat modest, since the main
bottleneck remains the evaluation function. However, the improvement remains,
and the coding effort needed is minimal; we will also see that it can be
combined with other techniques to reach a better speedup.

.. note::
   The cTools module is built at installation time (i.e. when executing the
   setup.py file). If no compiler is available, or if the building process
   failed for some reason, the cTools module will not be available.


Using an home-made C++ evaluation function
------------------------------------------

*Time taken : 33 seconds (4.5x faster)*
This time, we look at an heavier optimization : replacement of the evaluation
function by its C equivalent. CPython provides a C/C++ API to Python objects,
and allows the writing of a C extension module relatively easily. However,
this is problem specific, and can not be used with an other Python interpreter
than CPython (like PyPy).

In this case, the extension code has approximately 130 lines of C++ code, from
which about 100 are the evaluation function (the other parts are declarations
needed by the Python interpreter to build and use the extension). The module
is compiled with easy_install, and can thereafter be used as a normal Python
module :

  
.. literalinclude:: /code/tutorials/part_4/4_5_home_made_eval_func.py
   :lines: 28-28   
   
.. literalinclude:: /code/tutorials/part_4/4_5_home_made_eval_func.py
   :lines: 34-36

.. literalinclude:: /code/tutorials/part_4/4_5_home_made_eval_func.py
   :lines: 70-70

The speedup obtained is notable, up to 5 times faster. At this point, the part
of the computational effort taken by the evaluation drop from 80% to 10%. But
what makes the other 90%?

Combining C++ version of NSGA II and evaluation function
--------------------------------------------------------

*Time taken : 11 seconds (13.4x faster)*

For our last try, we use both the C version of NSGA-II and the C version of
the evaluation function. This time, we clearly see an impressive improvement
in term of computation speed, it is almost 15 times faster. This speed
brings DEAP in the same range of performances as compiled (static) programs
(like OpenBeagle): a small overhead is still produced by the systematic deep
copy of the individuals and the use of some pure Python functions, but this is
clearly not a bad performance at all considering that the program did not
changed that much.


Speedups summary
----------------

It should be noted that, apart the evaluation function, all the other steps of
the evolution (crossovers, mutations, copy, initialization, etc.) are still
programmed in Python, and thus benefit from its ease of use. Adding a
statistical measure or a sorting network viewer, trying other complicated
mutations operators, reading new individuals from a database or an XML file
and checkpointing the evolution at any generation is still far easier than
with any compiled evolution framework, thanks to the power of Python. So, by
adding a minimal complexity to the critical parts, one can still achieve
excellent performances without sacrificing the beauty of the code and its
clarity.

=============================== ========== =======
Method                          Time (s)   Speedup
=============================== ========== =======
Pure Python                     147        1.0x
PyPy 1.7                        36         4.1x
C++ NSGA II                     121        1.2x
Custom C++ evaluation function  33         4.5x
C++ NSGA II and C++ evaluation  11         13.4x
=============================== ========== =======

To complete this test, we also ran the problem with an harder parametrization
(16 inputs instead of 12). It took *1997 seconds* with standard python
interpreter, compared to *469 seconds* with PyPy (4.3x faster) and *124
seconds* when using C++ version for both NSGA II and evaluator, that is a
speedup of *16.1x*. In other terms, we reduced the computation time from more
than half an hour to a small 2 minutes...

=============================== ========== =======
Method                          Time (s)   Speedup
=============================== ========== =======
Pure Python                     1997        1.0x
PyPy 1.7                        469         4.3x
C++ NSGA II and C++ evaluation  124         16.1x
=============================== ========== =======


Distribution
------------

The previous optimizations were done by improving the execution speed itself.
To speed up the execution further, distribution might be a good solution,
especially if the computational effort is concentrated in a specific part of
the program (in evolutionnary algorithms, this is often the evaluation
function). DEAP offers some simple ways to distribute your code without
effort, look at the specific page :ref:`distribution-deap` to learn more about
it.
