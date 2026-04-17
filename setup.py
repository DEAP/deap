#!/usr/bin/env python

# read the contents of README file
from os import path
import codecs

import deap

try:
    from setuptools import setup, find_packages
    modules = find_packages(exclude=['examples'])
except ImportError:
    from distutils.core import setup
    modules = ['deap', 'deap.benchmarks', 'deap.tests', 'deap.tools']

this_directory = path.abspath(path.dirname(__file__))
long_description = codecs.open(path.join(this_directory, 'README.md'), 'r', 'utf-8').read()

setup(name='deap',
      version=deap.__revision__,
      description='Distributed Evolutionary Algorithms in Python',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='deap Development Team',
      author_email='deap-users@googlegroups.com',
      url='https://www.github.com/deap',
      packages=find_packages(exclude=['examples', 'tests']),
      platforms=['any'],
      keywords=['evolutionary algorithms', 'genetic algorithms', 'genetic programming', 'cma-es', 'ga', 'gp', 'es', 'pso'],
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
      install_requires=['numpy', 'moocore'],
      )
