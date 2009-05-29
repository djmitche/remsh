.. _introduction:

************
Introduction
************

This library supplies a small but complete collection of operations that a
"master" can cause to execute on a "slave".  The goals of the library are:

* Slaves are very simple and their definition stable

  * Slave installation is straightforward, and easily done without root access
  * Few or no external libraries are required to set up a slave

* The protocol is simple, well-defined, and language-agnostic.
* The master interface is simple, synchronous and thread-safe

Notice that the word "simple" appears several times in these goals.  This
library implements the minimal functionality to be complete.
