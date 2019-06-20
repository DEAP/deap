#!/usr/bin/env python
import sys

warnings = list()

try:
    from setuptools import setup, Extension, find_packages
    modules = find_packages(exclude=['examples'])
except ImportError:
    warnings.append("warning: using disutils.core.setup, cannot use \"develop\" option")
    from disutils.core import setup, Extension
    modules = ['deap', 'deap.benchmarks', 'deap.tests', 'deap.tools', 'deap.tools._hypervolume']

from setuptools.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, \
    DistutilsPlatformError

# read the contents of README file
from os import path
import codecs
this_directory = path.abspath(path.dirname(__file__))
long_description = codecs.open(path.join(this_directory, 'README.md'), 'r', 'utf-8').read()

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
        except DistutilsPlatformError as e:
            print(e)
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors as e:
            print(e)
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
          long_description=long_description,
          long_description_content_type="text/markdown",
          author='deap Development Team',
          author_email='deap-users@googlegroups.com',
          url='https://www.github.com/deap',
          packages=find_packages(exclude=['examples']),
        #   packages=['deap', 'deap.tools', 'deap.tools._hypervolume', 'deap.benchmarks', 'deap.tests'],
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
         ext_modules=extra_modules,
         cmdclass={"build_ext": ve_build_ext},
         install_requires=['numpy'],
         use_2to3=True
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

print("\n".join(warnings))
