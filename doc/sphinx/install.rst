============
Installation
============

BioTK is primarily tested and developed on Linux, and will likely work best
there. However, it is also possible to install on Windows using Cygwin. 

Vagrant VM
==========

The simplest option to test out BioTK is to use the prepared Vagrant VM image,
which can work on any operating system. First, install VirtualBox and Vagrant
from the following URLs, or using your system's package manager:

- https://www.virtualbox.org/wiki/Downloads
- http://www.vagrantup.com/downloads

Linux
=====

Ubuntu/Debian
-------------

To install on Ubuntu/Debian, execute the following commands in a shell:

.. code-block:: bash

    sudo apt-get install -y git
    git clone http://bitbucket.org/wrenlab/BioTK.git
    cd BioTK
    ./install/ubuntu.sh
    sudo pip3 install -r requirements.txt
    sudo python3 setup.py install
 
Arch Linux
----------

Execute these commands:

.. code-block:: bash

    sudo pacman -S --needed git
    git clone http://bitbucket.org/wrenlab/BioTK.git
    cd BioTK
    ./install/archlinux.sh
    sudo pip3 install -r requirements.txt
    sudo python3 setup.py install

Generic Linux or Linux without superuser privileges
---------------------------------------------------

First, clone the repository:

.. code-block:: bash

    git clone http://bitbucket.org/wrenlab/BioTK.git
    cd BioTK

You will need to ensure that you have Python version 3.2 or greater installed.
Also, the binary dependencies specified in the binary-dependencies.txt must be
installed and on your PATH.

Next, run:

.. code-block:: bash

    pip3 install -r requirements.txt  
    sudo python3 setup.py install

For a non-superuser install, run these commands instead:

.. code-block:: bash

    pip3 install --user -r requirements.txt
    python3 setup.py install --user

Windows
=======

TODO

Developer install
=================

A developer install will allow you to edit files in the BioTK/ directory and
have those changes take effect immediately without having to reinstall each
time. To do this, instead of:

.. code-block:: bash

    sudo python3 setup.py install

run,

.. code-block:: bash
    
    python3 setup.py develop --user

In order for scripts to be detected in this kind of install,
``$HOME/.local/bin`` must be on your ``$PATH``. (You can configure this in
``$HOME/.bashrc`` or your shell's equivalent).
