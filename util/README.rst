===============
BioTK utilities
===============

Generic utilities for data analysis that can be installed independently of
BioTK. (They are also required by BioTK).

Installation
============

Binary packages
---------------

It will be desirable to have precompiled Arch Linux and Debian/Ubuntu
packages, and possibly a Windows installer. Currently this is not implemented.

Dependencies
------------

Required dependencies
~~~~~~~~~~~~~~~~~~~~~

In addition to the GNU coreutils, which are included in any Linux distribution,
the following packages are needed:

- realpath
- awk (GNU)
- pixz
- lz4
- parallel (GNU parallel)

Installation will not proceed if any of these dependencies fail to be detected
(that is, they must be installed AND on your ``$PATH``).

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~

These dependencies are not necessary to use most of the utilities, but are
needed for full functionality. You will be warned if they are missing, but
installation will proceed:

- ucspi-tcp [xmatd]
- netcat (either OpenBSD or GNU version) [xmatc]
- mdbtools (for MS Access support)
- PostgreSQL client ("psql"; to access databases)

General instructions
--------------------

If you already have a POSIX environment (Linux, Cygwin, or possibly msysgit
[not tested]) with the dependencies installed, do the following:

From this directory, run:

    make DESTDIR=/usr/local install

Change DESTDIR to suit your needs; the default is ``$HOME/.local``, which does
not require root privileges. To use the utilities, $DESTDIR/bin needs to be
added to your PATH.

List of utilities
=================

Matrix manipulation
-------------------

- xmat: Store and query text matrices
- transpose: Transpose an arbitrarily large text matrix

Compression
-----------

- lzpaste: Like ``paste``, but works on LZ4 compressed files
