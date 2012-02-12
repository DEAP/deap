from distutils.core import setup, Extension

module1 = Extension('SNC',
                    sources = ['SNC.cpp'])

setup (name = 'SNC',
       version = '1.0',
       description = 'Sorting network evaluator',
       ext_modules = [module1]) 
