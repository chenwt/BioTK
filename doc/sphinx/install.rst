============
Installation
============

BioTK is primarily tested and developed on Linux, and will likely work best
there. However, it is also possible to install on Windows using Cygwin.

Linux
=====

Ubuntu/Debian
-------------

To install on Ubuntu/Debian, execute the following commands in a shell:

    sudo apt-get install -y git python3 python3-pip

Arch Linux
----------

Execute these commands:

    git clone git@bitbucket.org:wrenlab/BioTK.git
    cd BioTK
    sudo python3 setup.py install

You may be prompted for your superuser password or to enter other information
during the install process.

Generic Linux or Linux without superuser privileges
---------------------------------------------------

First, clone the repository:

    git clone git@bitbucket.org:wrenlab/BioTK.git
    cd BioTK

You will need to ensure that you have Python version 3.2 or greater installed,
as well as the binary dependencies specified in the binary-dependencies.txt
file. The steps for doing this will vary according to your distribution. Next,
run:

    pip3 install -r requirements.txt  
    sudo python3 setup.py install

For a non-superuser install, run these commands instead:

    pip3 install --user -r requirements.txt
    python3 setup.py install --user

Windows
=======

TODO
