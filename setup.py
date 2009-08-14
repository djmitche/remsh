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
      version=open("VERSION").read().strip(),
      description='Parallel remote shell operations in simple Python',
      author='Dustin J. Mitchell',
      author_email='dustin@zmanda.com',
      url='http://github.com/djmitche/remsh',
      packages=[
        'remsh',
        'remsh.master',
        'remsh.master.scripts',
        'remsh.master.slavelistener',
        'remsh.slave',
        'remsh.slave.scripts',
      ],
      entry_points = {
        'console_scripts': [
          'remsh-slave = remsh.slave.scripts.remsh_slave:main',
          'remsh-master = remsh.master.scripts.remsh_master:main',
        ],
      },
      test_suite='test',
      )
