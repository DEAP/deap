#!/usr/bin/env python
import sys
from distutils.core import setup, Extension
try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, \
    DistutilsPlatformError

try:
    from pypandoc import convert
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()
else:
    read_md = lambda f: convert(f, 'rst')

import deap

if sys.platform == 'win32' and sys.version_info > (2, 6):
   # 2.6's distutils.msvc9compiler can raise an IOError when failing to
   # find the compiler
   # It can also raise ValueError http://bugs.python.org/issue7511
   ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError,
                 IOError, ValueError)
else:
   ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)

class BuildFailed(Exception):
    pass

class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()

def run_setup(build_ext):
    extra_modules = None
    if build_ext:
        extra_modules = list()

        hv_module = Extension("deap.tools._hypervolume.hv", sources=["deap/tools/_hypervolume/_hv.c", "deap/tools/_hypervolume/hv.cpp"])
        extra_modules.append(hv_module)

    setup(name='deap',
          version=deap.__revision__,
          description='Distributed Evolutionary Algorithms in Python',
          long_description=read_md('README.md'),
          author='deap Development Team',
          author_email='deap-users@googlegroups.com',
          url='https://www.github.com/deap',
          packages=['deap', 'deap.tools', 'deap.tools._hypervolume', 'deap.benchmarks', 'deap.tests'],
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
         ext_modules = extra_modules,
         cmdclass = {'build_py': build_py, "build_ext" : ve_build_ext}
    )

try:
    run_setup(True)
except BuildFailed:
    print("*" * 75)
    print("WARNING: The C extensions could not be compiled, "
          "speedups won't be available.")
    print("Now building without C extensions.")
    print("*" * 75)

    run_setup(False)

    print("*" * 75)
    print("WARNING: The C extensions could not be compiled, "
          "speedups won't be available.")
    print("Plain-Python installation succeeded.")
    print("*" * 75)
