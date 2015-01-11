============
Installation
============

BioTK is primarily tested and developed on Linux, and will likely work best
there. However, it is also possible to install on OS X, or on Windows using
Cygwin, but these configurations are not tested, and some things likely will
not work.

Dependencies
============

BioTK requires a standard POSIX environment with the following additional
binary programs to be installed (the steps will be platform-specific):

- gzip
- GNU parallel
- cURL

Also, the following packages are needed for a few functions, but not required
for most functionality:

- pixz
- pigz
- Vowpal Wabbit
- gnumeric

For the C++ library:
- libhts
- libarmadillo
- zlib

Currently, a few pieces of BioTK functionality also depend on having the Kent
source utilities installed. These will be automatically installed for you, but
only on Linux 64-bit platforms, since that is the only platform they work on.
Hopefully these dependencies can be removed later. These are only necessary if
you want to query genomic intervals.

Finally, BioTK itself requires Python v3.4 or greater.

System requirements
===================

Some parts of BioTK require lots of RAM (at least 8GB total system RAM). Also,
some parts use a lot of temporary storage in your system's default temporary
directory (/tmp on Linux). Some Linux systems automatically mount /tmp to RAM,
but this can cause problems and should be disabled if it does (it is a bad idea
in general).

Installation
============

To install BioTK, you can use the ``pip`` package manager, which is installed
with newer Python versions.

For the latest stable version:

.. code-block:: bash

    pip3 install --user BioTK

For the development version:

.. code-block:: bash

    pip install --user git+git://bitbucket.org/wrenlab/BioTK.git

If you want a system-wide install, you can remove the ``--user`` flag and run
the above command as root, or prefix it with ``sudo``.

Developer install
=================

A developer install will allow you to edit files in the BioTK/ directory and
have those changes take effect immediately without having to reinstall each
time. To do this, instead of using pip, run:

.. code-block:: bash

    git clone http://bitbucket.org/wrenlab/BioTK.git
    cd BioTK
    python3 setup.py develop --user

In order for scripts to be detected in this kind of install,
``$HOME/.local/bin`` must be on your ``$PATH``. (You can configure this in
``$HOME/.bashrc`` or your shell's equivalent).
