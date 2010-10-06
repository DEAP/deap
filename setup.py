#!/usr/bin/env python

from distutils.core import setup

import eap

setup(name='DEAP',
      version=eap.__version__,
      description='Distributed Evolutionary Algorithms in Python',
      long_description='',
      author='Francois-Michel De Rainville, Felix-Antoine Fortin',
      author_email='',
      url='http://deap.googlecode.com',
      download_url='http://code.google.com/p/deap/downloads/list',
      packages=['eap'],
      platforms=['any'],
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
     )
