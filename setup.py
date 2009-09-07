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

import os

from setuptools import Command, setup, find_packages


class DocUpdate(Command):
    """
    Executes the upload-docs.sh from setuptools.
    """
    description = "Execute doc shell command"
    user_options = []

    initialize_options = finalize_options = lambda s: s
    run = lambda s: os.system('pushd doc/; sh upload-docs.sh; popd')


setup(name='remsh',
      version=open("VERSION").read().strip(),
      description='Parallel remote shell operations in simple Python',
      author='Dustin J. Mitchell',
      author_email='dustin@zmanda.com',
      url='http://github.com/djmitche/remsh',
      packages=find_packages('.', ['test']),
      entry_points = {
        'console_scripts': [
          'remsh-slave = remsh.slave.scripts.remsh_slave:main',
          'remsh-master = remsh.master.scripts.remsh_master:main',
        ],
      },
      test_suite='test',
      cmdclass = {'docupdate': DocUpdate},
      )
