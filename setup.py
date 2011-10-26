#!/usr/bin/env python

from distutils.core import setup, Extension

import deap

eap_ctools = Extension('deap.cTools',
                    sources = ['deap/cTools.cpp'])
#sn_cevaluator = Extension('evaluateSN_C',
                    #sources = ['examples/SNC.cpp'])
                    
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
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        ],
     ext_modules = [eap_ctools]
     )
