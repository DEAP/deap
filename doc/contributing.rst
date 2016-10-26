Contributing
============


Reporting a bug
---------------

You can report a bug on deap Github issues page.

`<https://github.com/deap/deap/issues>`_

Retrieving the latest code
--------------------------

You can check the latest sources with the command::

    git clone https://github.com/DEAP/deap.git


Contributing code
-----------------

The preferred way to contribute to deap is to fork the `main
repository <http://github.com/deap/deap/>`__ on GitHub,
then submit a "pull request" (PR):

 1. Fork the `project repository
    <http://github.com/deap/deap>`__: click on the 'Fork'
    button near the top of the page. This creates a copy of the code under your
    account on the GitHub server.

 2. Clone your fork locally::

        $ git clone git@github.com:YourLogin/deap.git

 3. Create a branch to hold your changes::

        $ git checkout -b my-feature

    and start making changes. Never work in the ``master`` branch!

 4. When you're done editing, do::

        $ git add modified_files
        $ git commit

    to record your changes in Git, then push them to GitHub with::

        $ git push -u origin my-feature

Finally, go to the web page of your fork of the deap repository,
and click 'Pull request' to send your changes for review.

You can also contact us on the deap users 
list at `<http://groups.google.com/group/deap-users>`_.

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

