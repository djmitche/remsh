Operations
==========

This section describes the RPC call or calls for each Remsh operation.  In each
case, only the method-specific box keys are described.

set_cwd
-------

The request box has the following key.

``cwd`` (optional)
    requested new working directory; this may be a partial path, in which case
    it is relative to the current directory

If the ``cwd`` key is omitted, then the request is to revert to the default
working directory.  An empty (but present) ``cwd`` is a request to return the
current directory without changing it.

The response box has the following key.

``cwd``
    resulting working directory; this should be an absolute path

mkdir
-----

The request box has the following key:

``dir``
    directory to create

The response box is empty.

unlink
------

The request box has the following key:

``file``
    file to unlink

The response box is empty.

execute
-------

The request box has the following keys:

``args``
    list of command-line arguments, separated with 0 bytes.

``want_stdout``
    ``y`` if ``data`` calls should be made with data from stdout, otherwise
    ``n``

``want_stderr``
    ``y`` if ``data`` calls should be made with data from stderr, otherwise
    ``n``

The response is an empty box.  After the response, the slave side makes zero or
more ``data`` calls, none of which require a response, and exactly one
``finished`` call, which also does not require a response.  A ``data`` request
represents some quantity of output data from the spawned process, and has the
following keys:

``stream``
    the name of the stream that produced the data (``stderr`` and ``stdout``
    are the standard streams)

``data``
    one or more bytes of data

The ``finished`` request has the following key:

``result``
    exit value for this process, in decimal notation

send
----

The initial request box has the following key:

``dest``
    destination filename on the slave system

The response is an empty box.  Once the response is received, the master side
makes a series of ``data`` calls, where each has the following key:

``data``
    one or more bytes of data

The data stream is terminated by a ``finished`` request, which is empty, and to
which the slave replies with an empty response (or an error response).

Note that there is no provision to indicate an error during the data
transmission phase.  If an error (e.g., running out of disk space) does occur,
the slave must continue to read and discard ``data`` boxes until the
``finished`` box arrives, and then signal the error in the response box.

fetch
-----

The initial request box has the following key:

``src``
    source filename on the slave system

The response is an empty box.  Once the response is received, the slave side
makes a series of ``data`` calls identical to those for ``send``.

The data stream is terminated by a ``finished`` request, this time from the
slave to the master.  This request has the following key:

``errmsg`` (optional)
    the slave-side error message

The response from the server is empty.

As with ``send``, there is no provision to indicate an error during data
transmission.  If a problem occurs on the master, it must continue to read and
discard ``data`` boxes and reply to the terminating ``finished`` box.  The
error message should not be sent to the slave.  If a problem occurs on the
slave, it should stop sending ``data`` boxes and send a ``finished`` box
containing the optional ``errmsg`` key with a suitable error message.

rmtree
------

The request has the key,

``tree``
    root of the directory tree to remove

and the response is an empty box or an error.

TODO
''''

* optionally translate platform-specific newlines to '\n' in execute, send, etc.
* provide a more generic list-of-strings thing, and quote NUL bytes in it
* support additional watched files
* should send include some chance for the slave to indicate error?
* support sending a literal string with send()
