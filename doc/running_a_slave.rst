.. _running_a_slave:

***************
Running a Slave
***************

If you'd like to set up a *remsh* slave to provide shell access to a project,
you've come to the right place.

Eventually, several options will be available.  At the moment, the only slave
implementation is in Python:

============
Python Slave
============

The Python slave has minimal requirements, beside Python itself -- version 2.3.5 or later.

Next, install setuptools if it is not already present.  This may be done via a
distribution package (probably named ``setuptools``), or see
http://peak.telecommunity.com/DevCenter/EasyInstall for more detailed
instructions.

Once setuptools is installed, run::

    easy_install remsh

This will download and install remsh's requirements and install them.  You
should then find the ``remsh-slave`` command available in your shell::

    remsh-slave master.host.com 9876

This command will connect to the master on ``master.host.com`` port ``9876``
and execute whatever commands it directs.
