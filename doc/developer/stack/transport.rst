Transport Layer
===============

The transport layer provides a stream-based interface to the wire layer.  It
also provides authentication, encryption, and reliability.

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
