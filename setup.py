#!/usr/bin/env python
# This file is part of remsh.
#
# remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with remsh.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup(name='remsh',
      version='0.5', # 1.0 will be when it's got all of the ops implemented!
      description='Parallel remote shell operations in simple Python',
      author='Dustin J. Mitchell',
      author_email='dustin@zmanda.com',
      install_requires=['zope.interface'],
      url='http://github.com/djmitche/remsh',
      packages=[
        'remsh',
        'remsh.master',
        'remsh.master.slavelistener',
        'remsh.slave',
      ],
      scripts=[
        'scripts/remsh-slave',
        'scripts/remsh',
      ],
      test_suite='test',
      )
