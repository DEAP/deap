#!/usr/bin/python
""" 
Simple script to automatically create the Netbeans Project folder
and files. It selects the default python version as the interpreter.
This can then be changed by modifying the project option in Netbeans.
"""

from __future__ import with_statement # just for < Python 2.6

import os
import sys
from string import Template

prop_template = Template("""java.lib.path=
platform.active=Python_$version
python.lib.path=
src.dir=$src
""")

xml_template = Template("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://www.netbeans.org/ns/project/1">
    <type>org.netbeans.modules.python.project</type>
    <configuration>
        <data xmlns="http://nbpython.dev.java.net/ns/php-project/1">
            <name>$name</name>
            <sources>
                <root id="src.dir"/>
            </sources>
            <tests/>
        </data>
    </configuration>
</project>""")

project_name = os.getcwd().rpartition('/')[2]
project_src = os.getcwd() + '/src'
python_version = sys.version.partition(" ")[0]

xml_string = xml_template.substitute(name=project_name)
prop_string = prop_template.substitute(version=python_version, src=project_src)

if not os.path.exists('nbproject'):
    os.makedirs('nbproject')

with open('nbproject/project.properties', 'w') as properties:
    properties.write(prop_string)
with open('nbproject/project.xml', 'w') as xml:
    xml.write(xml_string)

