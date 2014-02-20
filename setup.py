#!/usr/bin/env python
import sys
from distutils.core import setup
try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

import deap

setup(name='deap',
      version=deap.__revision__,
      description='Distributed Evolutionary Algorithms in Python',
      long_description=open('README.txt').read(),
      author='deap Development Team',
      author_email='deap-users@googlegroups.com',
      url='http://deap.googlecode.com',
      packages=['deap', 'deap.tools', 'deap.benchmarks', 'deap.tests'],
      platforms=['any'],
      keywords=['evolutionary algorithms','genetic algorithms','genetic programming','cma-es','ga','gp','es','pso'],
      license='LGPL',
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        ],
     ext_modules = [],
     cmdclass = {'build_py': build_py}
)
