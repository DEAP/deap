Contributing
============


Reporting a bug
---------------

You can report a bug on the issue list on google code.

`<http://code.google.com/p/deap/issues/list>`_

Retrieving the latest code
--------------------------

You can check the latest sources with the command::

    hg clone https://deap.googlecode.com/hg

If you want to use the development version, you have to update the repository
to the developing branch with the command::

    hg update dev

Contributing code
-----------------

Contact us on the deap users list at `<http://groups.google.com/group/deap-users>`_.

Coding guidelines
-----------------

Most of those conventions are base on Python PEP8.

    *A style guide is about consistency. Consistency with this style guide is important.
    Consistency within a project is more important. Consistency within one module or 
    function is most important.*

Code layout
+++++++++++

Same as PEP8.

Imports
+++++++

First imports in a file are the standard library module, then come the imports of eap module, and finally the custom module for a problem. Each block of imports should be separated by a new line.

::

  import system
  
  from deap import base

  import mymodule

Whitespace in Expressions and Statements
++++++++++++++++++++++++++++++++++++++++

Same as PEP8.

Comments
++++++++

Same as PEP8

Documentation Strings
+++++++++++++++++++++
Same as PEP8

Naming Conventions
++++++++++++++++++

- **Module** : use the lowercase convention.
- **Class** : class names use the CapWords? convention.
- **Function** / Procedure : use the mixedCase convention. First word should be an action verb.
- **Variable** : use the lower_case_with_underscores convention.

