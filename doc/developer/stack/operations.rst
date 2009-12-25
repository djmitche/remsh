Operations Layer
================

The operations layer makes use of the wire layer to get real work done on the
slave.  The operations layer is *not* symmetrical, and has two implementations:
master-side and slave-side.  The master side provides a means to invoke each
operation, while the slave side implements each operation.  There is at most
one implementation of this layer on each side, in each language.

API
---

The slave side API is simply a loop that performs operations sequentially,
given a wire-layer object.  The specifics are implementation-dependent.

The master side provides an object that represents the slave, with a method for
each operation.  The constructor takes a wire instance that is already
connected to a slave.  At any time, at most one operation may be in progress on
a given wire connection.

Each method is described below, although the language-specific details of the
argument and return values are not covered here.  Note that the operation
methods all block until the operation is complete.

The meaning of each operation is described in :ref:`using-remsh`, and is not
duplicated here.

Protocol
--------

The operations are all defined in terms of a sequences of boxes sent between
the master and slave.  At all times, the master and slave operation
implementations agree on which side will send the next box.  Initially and at
the completion of each operation, the slave awaits a box from the master. 

The initial box for each operation has a ``meth`` key which should be used by
the slave to determine which method was invoked.  Method names are given in
lower-case ASCII characters.  The box also has a ``version`` key, which gives
the version of the protocol in use by the master.  Slave implementations must
reject any request with a version higher than they support, and should
implement lower-version requests wherever possible.  The sequence of boxes for
each method is described in the "Operations" section, below.  

Error Handling
..............

When an error occurs while executing an operation on the slave side, the slave
must send an error box, which can be identified by having an ``error`` key.  It
has the following keys:

``error``
    A string describing the error

``errtag``
    A short ASCII string identifying the type of error, as described for the
    particular operation below.  If no matching tag is available, then
    ``errtag`` should be the string ``unknown``.  The master-side
    implementation may use the error tag to map errors onto language-specific
    exceptions.  The master should treat any unrecognized error tag as
    ``unknown``.

After an error box, the next box will be sent by the master to begin a new
operation.

The following error tags can be returned any time an error box is allowed:

``invalid-meth``
    The slave does not implement the method in the request box.

``version-too-new``
    The given ``version`` is higher than the highest version the slave supports.

``version-unsupported``
    The given ``version`` is not supported by the slave, but the slave does support
    higher versions.

``invalid``
    The request was invalid for any reason not convered by a more specific error tag.

Operations
..........

set_cwd
+++++++

The ``set_cwd`` method takes a single, optional argument, ``cwd``, and returns a
string.  The master sends a box with the following keys:

``version``
    ``1``

``meth``
    ``set_cwd``

``cwd`` (optional)
    requested new working directory; this may be a partial path, in which case
    it is relative to the current directory

If the ``cwd`` key is omitted, then the request is to revert to the default
working directory.  An empty (but present) ``cwd`` is a request to return the
current directory without changing it.

The response box from the slave has the following key.

``cwd``
    resulting working directory; this should be an absolute path

The following error tags may be returned:

``notfound``
    The new directory could not be found

getenv
++++++

The ``getenv`` method takes no arguments, and returns a set of key/value pairs.

The request box has a single key:

``version``
    ``1``

``meth``
    ``getenv``
    
The response box has a key for each environment variable, where the key
consists of the suffix ``env_`` concatenated with the name of the variable.  If
the value of an environment variable is greater than 65535 bytes, it is
silently truncated.  There is no limit to the number of environment variables
which can be returned.

This operation does not return any unique error tags.

mkdir
+++++

The ``mkdir`` method takes a single argument, ``dir``, and returns nothing.

The request box has the following keys:

``version``
    ``1``

``meth``
    ``mkdir``

``dir``
    directory to create

The response box is empty.

The following error tags may be returned:

TODO

execute
+++++++

The ``execute`` method takes a number of arguments: ``args``, a list of
arguments; and ``want_stdout`` and ``want_stderr``, booleans.  The request box
has the following keys:

``version``
    ``1``

``meth``
    ``execute``

``args``
    list of command-line arguments, separated with NUL bytes.

``want_stdout``
    ``y`` if ``data`` calls should be made with data from stdout, otherwise
    ``n``

``want_stderr``
    ``y`` if ``data`` calls should be made with data from stderr, otherwise
    ``n``

The response is an empty box.  After the response, the slave side sends zero or
more data boxes, and exactly one result box.  A data box represents some
quantity of output data from the spawned process, and has the following keys:

``stream``
    the name of the stream that produced the data (``stderr`` and ``stdout``
    are the standard streams)

``data``
    one or more bytes of data

The result box can be distinguished from a data box by having a ``result`` key:

``result``
    exit value for this process, expressed as a decimal integer

At any time, the slave may send an error box, terminating the operation.  The
following error tags may be returned:

TODO

TODO
````

* optionally translate platform-specific newlines to '\n' in execute, send, etc.
* provide a more generic list-of-strings thing, and quote NUL bytes in it
* support additional watched files

send
++++

A send operation is initiated by a box with these keys:

``version``
    ``1``

``meth``
    ``send``

``dest``
    destination filename on the slave system

The response from the slave is an empty box (meaning "go ahead"), or an error
box.  Once the empty box is received, the master side sends a series of data
boxes, where each has the following key:

``data``
    one or more bytes of data

The data stream is terminated by an empty box, and to which the slave replies
with an empty box (or an error response).

Note that there is no provision to indicate an error during the data
transmission phase.  If an error (e.g., running out of disk space) does occur,
the slave must continue to read and discard data boxes until an empty box
arrives, and then send the error box.

The following error tags may be returned:

TODO

TODO
````

* should send include some chance for the slave to indicate error?
* support sending a literal string with send()

fetch
+++++

The initial box from the master has the following keys:

``version``
    ``1``

``meth``
    ``fetch``

``src``
    source filename on the slave system

The slave responds by sending a series of data boxes identical to those for
the *send* operation.  The data stream is terminated by an emtpy box, this time
from the slave to the master.  If it
encounters an error, the slave can send an error box at any time, terminating
the tranfer.

As with ``send``, there is no provision to indicate an error during data
transmission.  If a problem occurs on the master, it must continue to read and
discard data boxes and reply to the terminating empty box.  The
error message should not be sent to the slave.  

The following error tags may be returned:

TODO

remove
++++++

The initial box from the master has the following keys:

``version``
    ``1``

``meth``
    ``remove``

``path``
    path to the file or directory to remove

and the response from the slave is an empty box or an error.

The following error tags may be returned:

TODO

rename
++++++

The request has the following keys:

``version``
    ``1``

``meth``
    ``rename``

``src``
    pathname of the file or directory to move

``dest``
    pathname to which it should be moved

and the response from the slave is an empty box or an error.

The following error tags may be returned:

TODO

copy
++++

The request has the following keys:

``version``
    ``1``

``meth``
    ``copy``

``src``
    pathname of the file to copy

``dest``
    pathname to which it should be copied

and the response from the slave is an empty box or an error.

The following error tags may be returned:

TODO

stat
++++

The request has the following key:

``version``
    ``1``

``meth``
    ``stat``

``pathname``
    pathname to stat

and the response is a box with the following key (or an error):

``result``
    one of ``d``, ``f``, or an empty string

The following error tags may be returned:

TODO

