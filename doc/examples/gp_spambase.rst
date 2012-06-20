.. _spambase:
    
===================================
Spambase Problem: Strongly Typed GP
===================================

This problem is a classification example using STGP (Strongly Typed Genetic Programming). The evolved programs work on floating-point values AND Booleans values. The programs must return a Boolean value which must be true if e-mail is spam, and false otherwise. It uses a base of emails (saved in *spambase.csv*, see :ref:`refPapersSpam`), from which it randomly chooses 400 emails to evaluate each individual.

.. warning::
    Don't expect too much from this program as it is quite basic and not oriented toward performance. It is given to illustrate the use of strongly-typed GP with DEAP. From a machine learning perspective, it is mainly wrong.

Primitives set
==============

Strongly-typed GP is a more generic GP where each primitive, in addition to have an arity and a corresponding function, has also a specific return type and specific parameter(s) type. In this way, each primitive is someway describe as a pure C function, where each parameter has to be one of the good type, and where the return value type is specified before run time.

.. note::
    Actually, when the user does not specify return or parameters type, a default type is selected by DEAP. On standard GP, because all the primitives use this default type, this behaves as there was no type requirement.
    
We define a typed primitive set almost the same way than a normal one, but we have to specify the types used.
    
.. literalinclude:: /code/examples/gp/gp_spambase.py
   :lines: 35-66

On the first line, we see the declaration of a typed primitive set with :class:`~deap.gp.PrimitiveSetTyped`. The first argument remains the set name, but the next ones are the type of the entries (in this case, we have 57 float entries and one Boolean output; we could have written `float` 57 times, but it is fairly quicker and more understandable to use the :func:`itertools.repeat` function). The last argument remains the entries prefix.

After that, we define the primitives themselves. The definition of a typed primitive has two additional parameters : a list containing the parameters type, in order, and the return type.

.. note::
    The types specified do not have to be real Python or C types. In the above example, we may rename "float" in "type1" and "bool" in "type2" without any issue. For the same reason, DEAP nor Python actually check if a given parameter has the good type.

The terminals set is then filled, with at least one terminal of each type, and that is for the primitive set declaration.

Evaluation function
===================

The evaluation function is very simple : it picks 400 mails at random in the spam database, and then checks if the prediction made by the individual matches the expected Boolean output. The count of well predicted emails is returned as the fitness of the individual (which is so, at most, 400).

.. literalinclude:: /code/examples/gp/gp_spambase.py
   :pyobject: evalSpambase


Toolbox
=======

The toolbox used is very similar to the one presented in the symbolic regression example, but notice that we now use specific STGP operators for crossovers and mutations :

.. literalinclude:: /code/examples/gp/gp_spambase.py
   :lines: 86-90
    

Conclusion
================

Although it does not really differ from the other problems, it is interesting to note how Python can decrease the programming time. Indeed, the spam database is in csv form : with many frameworks, you would have to manually read it, or use a non-standard library, but with Python, you can use the built-in module :mod:`csv` and, within 2 lines, it is done! The data is now in the matrix *spam* and can easily be used through all the program :

The complete example: [`source code <code/gp/gp_spambase.py>`_]

.. _refPapersSpam:
    
Reference
=========

Data are from the Machine learning repository, http://www.ics.uci.edu/~mlearn/MLRepository.html
