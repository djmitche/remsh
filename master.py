#! python
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

import sys
import time
import socket
from remsh import slavemgr


def main():
    slavemgr.SlaveManager(52444).start()

    import time
    while 1:
        time.sleep(5)

main()
