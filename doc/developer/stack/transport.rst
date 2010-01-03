Transport Layer
===============

The transport layer provides a stream-based interface to the wire layer.  It
also provides authentication, encryption, and reliability.  The layer is
composed of several sublayers:

  1. TCP socket
  2. bytestream
  3. reliability
  4. authentication

In general, the initialization portion of each sublayer is asymetrical, but
once established, the operation is symmetrical.

TCP Socket
----------

All transport takes place, over a TCP socket.  The initiator of this connection
is undefined: implementations must either support connecting to another
implementation, or listening for incoming connections, and if possible should
support both.

Once a connection is established, the master sends an 8-byte greeting to the
slave::

  R  E  M  S  H  -  M  \n
  52 45 4D 53 48 2D 4D 0A

A slave should reject a connection which does not begin with these bytes.  The
slave then responds with::

  R  E  M  S  H  -  S  \n
  52 45 4D 53 48 2D 53 0A

The master should reject a connection where it does not receive this response
in a timely fashion.  These headers identify the master (``M``) and slave
(``S``) sides of the connection, and provide a user-friendly textual banner
to identify the protocol in use.  The TCP sokect initialization is complete.

Bytestream
----------

The slave then sends a series of supported bytestream capabilities represented
by single bytes, terminated by a zero byte.  The defined capabilities are::

``00``
    no more capabilities

``01`` - TLS
    slave supports TLS at the bytestream sublayer

The master responds with a series of bytestream capabilities that will be used
on the connection.  This is always a subset of the capabilities advertised by
the slave.

If the TLS capability was agreed upon in the TCP socket initialization, then
both sides immediately enter encrypted mode.

TODO - details

If TLS is enabled, any subsequent communication takes place over the encrypted
channel; otherwise, communication proceeds on the raw TCP channel.

Reliability
-----------

The reliability sublayer presents a unified "session" to higher sublayers,
which may span multiple bytestreams, if both sides support this behavior.  It
keeps a count of incoming and outgoing bytes in the session, and can retransmit
un-received bytes in the event of a failure at a lower level.  The sublayer
also allows for periodic "keepalive" packets, which can be sent during quiet
times in the connection to allow TCP to detect any connection failures.

TODO - finish this (just use 0 for now)

The reliability layer assigns a 16-byte identifier to each direction of each
bytestream.  Subsequent bytestreams in the same session are identified by
giving the identifier of the previous bytestream.

Reliability negotiation begins with the master sending either a zero byte
(indicating no reliability support) or a packet with the following format::

    01 - reliability protocol version number
    (16 bytes) - previous bytestream identifier
    (16 bytes) - nonce

The slave replies with a similar packet, or with a zero byte if reliability is
not supported.  If the master indicated no reliability support, then the slave
must respond with a zero byte.

In the master's negotiation packet, the "previous bytestream hash" is an MD5 hash 

...

If no reliability was negotiated, then subsequent communications take place
with no encapsulation.
