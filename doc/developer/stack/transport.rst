Transport Layer
===============

The transport layer provides a stream-based interface to the wire layer.  It
also provides authentication, encryption, and reliability.

API
---

The connection-setup phase of the API is implementation-specific, including any
authentication and encryption setup.  Once that is complete, though, the caller
is left with a "connected" transport object, which is symmetric from the
perspective of this API.  This object has a ``read`` method that will read an
arbitrary amount of data from the connection, and a ``write`` method that will
write data to the connection.  Both methods are synchronous and unbuffered:
reads must block until data is available, and any data written to the
connection must be sent before the method returns.

To close a connection, use the object's ``close`` method.  The object is
considered completely unusable after this method is called.  The ``read``
method indicates that the remote end has closed the connection by returning a
zero-length buffer.

TODO: async interface

Protocols
---------

Several protocols are defined here.  Implementations must support
slave-initiated TCP, and should support any other protocols that are practical
on the platform in question.

Note that there is no provision for negotiating transport protocol - the slave
and master must both be configured for the same protocol.

Slave-Initiated TCP
'''''''''''''''''''

In this protocol, the slave initiates a TCP/IP connection to the master on a
pre-configured port.  Once the connection is established, the master sends the
five ASCII characters ``remsh`` followed by a newline (0x0a).

The slave responds by sending a username and password, each terminated by a
newline.  If no authentication is configured, then the username ``anonymous``
should be employed, with an empty password.
