RPC
===

Remsh's RPC implementation is layered atop the low-level wire protocol classes
like :class:`~remsh.amp.wire.SimpleWire`.  This implementation is intended to
interoperate with the Twisted RPC library, but with a few important
restrictions:

* remote calls cannot be interleaved - one call must finish before the next
  begins
* both sides of the communication channel must always agree on which side will
  initiate the next remote call

Protocol
--------

The RPC protocol specifies a "call" as a request box paired with a response
box.  The request has two special keys: ``_command`` specifies the desired
remote method, while ``_ask`` specifies a unique cookie to identify this
request.  The cookie is redundant in this implementation, since at most one
outstanding request can exist at any time, but is included for compatibility
with the Twisted implementation.  Any other keys are passed as arguments to the
called procedure.

A response box contains a ``_answer`` key giving the same cookie that was
supplied with ``_ask``, and any other keys make up the procedure's return
value.  If an exception is raised during remote execution, then the response
box instead has keys ``_error``, giving the cookie, ``_error_description``,
describing the error, and ``_error_code`` giving a numeric code for the error.
Within Remsh, the error code is ignored on receipt and is set to zero on
transmission.

This entire process requires one network round trip, and because interleaved
requests are not allowed, pipelining is not possible.  To reduce latency, both
sides can agree that certain requests do not require an answer.

Implementation
--------------

.. class:: remsh.amp.rpc.RemoteError

    Exception representing an error on the remote system.  The exception
    object's ``args[0]`` contains the ``_error_description`` from the response
    box.

.. class:: remsh.amp.rpc.RPC(wire)

    :param wire: wire implementation on which to layer the RPC
    :type wire: :class:`~remsh.amp.wire.SimpleWire` or subclass

    Implements an RPC connection atop an arbitrary wire-level implementation.

    To respond to incoming procedure calls, subclass `RPC` and name methods
    available for remote invocation with the prefix ``remote_``.  Such methods
    will be invoked with the request box as parameter, and should call
    :meth:`~remsh.amp.rpc.RPC.send_response` with a response box, if one is
    expected.  If the method raises :class:`~remsh.amp.rpc.RemoteError`, the
    error will be propagated to the remote caller, but the exception must not
    be raised after :meth:`~remsh.amp.rpc.RPC.send_response` is invoked.  Any
    other exceptions will be handled locally.

    For example::

        def remote_tolower(self, rq):
            str = rq['str']
            if str == '':
                raise RemoteError("can't call tolower on an empty string")
            str = str.lower()
            self.send_response({'str' : str})

    .. method:: call_remote(method, **kwargs)

        :param method: method name to invoke
        :param kwargs: arguments to the remote method (keys and values will be stringified)
        :raises: :class:`~remsh.amp.rpc.RemoteError` for remote exceptions
        :raises: :class:`~remsh.amp.wire.Error` for protocol errors
        :raises: :class:`socket.error` for socket errors

        Invoke a remote method.  This method blocks until it receives a
        response, and raises :class:`~remsh.amp.rpc.RemoteError` or returns the
        response box, as appropriate.

    .. method:: call_remote_no_answer(method, **kwargs)

        :param method: method name to invoke
        :param kwargs: arguments to the remote method (keys and values will be stringified)
        :raises: :class:`~remsh.amp.rpc.RemoteError` for remote exceptions
        :raises: :class:`~remsh.amp.wire.Error` for protocol errors
        :raises: :class:`socket.error` for socket errors

        Same as ``call_remote``, but do not wait for an answer.

    .. method:: handle_call(**handlers)

        :param handlers: handlers for procedures that are not implemented as ``remote_`` methods
        :raises: :class:`~remsh.amp.wire.Error` for protocol errors
        :raises: :class:`socket.error` for socket errors
        :raises: :class:`EOFError` on EOF in the middle of a box
        :raises: any exception from the ``remote_`` method except
                 :class:`~remsh.amp.rpc.RemoteError`

        Handle exactly one invocation of a local method by the remote system.

        The names of the handlers in ``handlers`` should include the
        ``remote_`` prefix, and the functions should expect a single argument -
        the request box.  For example::

          def remote_data(rq):
            print rq['data']
          rpc.handle_call(remote_data=remote_data)

    .. method:: send_response(box)

        :param box: the box to send as a response

        Called from a ``remote_`` method, this sends a response to an RPC
        request.  This must not be called twice, and the remote method must not
        raise :class:`~remsh.amp.rpc.RemoteError` after this
        :meth:`send_response` is called.
