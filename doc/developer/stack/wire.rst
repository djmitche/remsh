Wire Layer
==========

The wire layer provides a very simple interface to higher layers.  It is
symmetrical - the slave and master both use the same source.  It provides a way
to send and receive "boxes", which are small sets of key/value pairs.

Boxes are sent to the other side of the connection, in order and without loss.

API
---

This layer is represented as an object, the constructor for which takes a
reference to a transport object.  The object has two methods: ``send_box`` and
``read_box``.  The first takes a box to be transmitted to the remote side, and
the second returns a box from the remote side, blocking until the box is
received.  The ``close`` method closes the underlying transport object.

Boxes are implemented in a language-specific fashion.

Protocol
--------

All remsh implementations must support an implementation of the wire layer
using AMP, and may support other implementations.  The user must explicitly
configure any alternative implementations on both the master and slave.
Without any such configuration, implementations must assume that AMP is in use.

AMP is the `Asynchronous Messaging Protocol
<http://twistedmatrix.com/documents/current/api/twisted.protocols.amp.html>`_,
a message-based protocol designed by the folks at Twisted Matrix.  This
protocol operates over the transport layer, adding its own framing.

Of the details described in the link above, remsh uses only the AMP wire
protocol, because it is a simple protocol that can be implemented with minimal
code in any language.  Remsh does not exploit the asynchronous nature of the
protocol, however: in general, both sides of a connection always know which
side will send the next message.

An AMP "box" is a sequence of key-value pairs, with unique keys.  Both keys and
values are arbitrary 8-bit bytestrings with no particular encoding specified.
A box is represented in a bytestream by alternating keys and values, each
prefixed with a 2-byte length, with an empty key signalling the end of a box.
The lengths are specified in network byte order.  Key order in the bytestream
is irrelevant, and duplicate keys are not allowed.

Boxes are often written as Python dictionaries in this documentation, for
brevity.

For example, the box ::

  { 'height' : '10cm', 'width' : '12cm' }

Can be represented as ::

  00 05             key length
  77 69 64 74 68    "width"
  00 04             value length
  31 32 63 6D       "10cm"
  00 06             key length
  68 65 69 67 68 74 "height"
  00 04             value length
  31 30 63 6D       "10cm"
  00 00             box terminator

Key lengths must be less than 256, so the leading byte is always ``00``.

Note that this places an upper limit on the size of a value (64k), and as a
consequence reasonable limits on the overall size of a box are possible (based
on the largest number of allowed keys in a remsh box), for security- or
memory-conscious uses.
