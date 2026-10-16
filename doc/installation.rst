Installation
============

Requirements
------------

DEAP uses Python 3. The CI test matrix covers Python 3.10 through 3.14.
Numpy_ and moocore_ are required dependencies and are installed automatically by
pip. The source is already Python 3 code: installation does not run 2to3 and
does not require downgrading setuptools. For distributed evaluation, DEAP can
use SCOOP_. We recommend matplotlib_ for visualization of results as it is
fully compatible with DEAP's API.

.. _SCOOP: http://www.pyscoop.org/
.. _Numpy: http://www.numpy.org/
.. _moocore: https://pypi.org/project/moocore/
.. _matplotlib: http://www.matplotlib.org/


Install DEAP
------------

We encourage you to use easy_install_ or pip_ to install DEAP on your system.
Linux package managers like apt-get, yum, etc. usually provide an outdated
version. ::

   easy_install deap

or ::

   pip install deap

If you wish to build from sources, download_ or clone_ the repository and type::

   python setup.py install

.. _download: https://pypi.python.org/pypi/deap/
.. _clone: https://github.com/DEAP/deap.git

.. _easy_install: http://pythonhosted.org/distribute/easy_install.html
.. _pip: http://www.pip-installer.org/en/latest/
