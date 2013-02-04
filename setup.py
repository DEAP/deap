#!/usr/bin/env python
import sys
from distutils.core import setup, Extension
try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

import deap

ext_modules = []
if "--with-ctools" in sys.argv:
    ext_modules.append(Extension('deap.cTools', ['deap/cTools.cpp']))
    sys.argv.remove("--with-ctools")

setup(name='deap',
      version=deap.__revision__,
      description='Distributed Evolutionary Algorithms in Python',
      long_description=open('README.txt').read(),
      author='deap Development Team',
      author_email='deap-users@googlegroups.com',
      url='http://deap.googlecode.com',
      download_url='http://code.google.com/p/deap/downloads/list',
      packages=['deap', 'deap.benchmarks', 'deap.dtm', 'deap.tests'],
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
     ext_modules = ext_modules,
     cmdclass = {'build_py': build_py}
)