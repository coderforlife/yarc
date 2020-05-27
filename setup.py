"""
This file is part of YARC (https://github.com/coderforlife/yarc).
Copyright (c) 2019 Jeffrey Bush.

This program is free software: you can redistribute it and/or modify  
it under the terms of the GNU General Public License as published by  
the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
General Public License for more details.

You should have received a copy of the GNU General Public License 
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from setuptools import setup
import sys, os

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "README.md"), 'r') as f:
    long_description = f.read()

setup(
    name='yarc',
    version='0.9.3',
    description='Yet Another Roomba Controller',
    license="GPLv3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Jeffrey Bush',
    author_email='jeff@coderforlife.com',
    url="https://github.com/coderforlife/yarc",
    packages=['yarc'],
    install_requires=['pyserial'] + [['aenum'] if sys.version_info < (3, 6) else []],
    python_requires='>=3.5',
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Topic :: System :: Hardware",
    ],
)
