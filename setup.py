#!/usr/bin/env python
# This file is part of Remsh.
#
# Remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Remsh.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup(name='Remsh',
      version='1.0',
      description='Parallel remote shell operations in simple Python',
      author='Dustin J. Mitchell',
      author_email='dustin@zmanda.com',
      install_requires=['zope.interface'],
      #url='http://www.python.org/sigs/distutils-sig/',
      packages=[
        'remsh',
        'remsh.master',
        'remsh.master.slavelistener',
        'remsh.slave',
      ],
      scripts=[
        'scripts/remsh-slave',
        'scripts/remsh',
      ]
      )
