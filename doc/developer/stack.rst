Network Stack
=============

Remsh implements a network stack of its own, with three layers:

* The *transport* layer takes care of getting data between master and slave,
  and also provides connection setup and authentication support.  In many cases
  this layer provides some level of reliability.

* The *wire* layer handles framing of boxes (messages) between the master and
  slave, using an underlying transport layer.  This layer can also provide
  reliability.

* The *operations* layer implements the remsh operations - executing commands,
  uploading and downloading files, etc. - on top of the wire layer.

The following sections describe this stack in a language-agnostic fashion.
Language-specific descriptions appear below.

.. toctree::
   :maxdepth: 2

   stack/transport
   stack/wire
   stack/operations
