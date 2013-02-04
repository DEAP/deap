from distutils.core import setup, Extension

module1 = Extension('AntC',
                    sources = ['AntSimulatorFast.cpp'])

setup (name = 'AntC',
       version = '1.0',
       description = 'Fast version of the Ant Simulator (aims to replace the AntSimulator class)',
       ext_modules = [module1]) 
