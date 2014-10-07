=============
Configuration
=============

BioTK can serve as a simple set of scripts and APIs, but also has the ability
to download, process, and integrate many publicly available biomedical
datasets, such as GEO and MEDLINE.

Global configuration of BioTK is done through a `YAML
<http://yaml.org/>`_-format file called ``BioTK.yml``. This file contains such
information as database connection parameters, data directory locations,
logging, and allows you to enable or disable certain features of BioTK. It
**does not**, however, directly affect the behavior of scripts or their
results. These kinds of settings are supplied to each script individually.

Configuration is not necessary to use the basic functionality of BioTK.

Configuration file location
---------------------------

On startup, BioTK will check the following locations, in
order, for this configuration file:

- The current directory
- ``$HOME/.BioTK.yml``
- ``$HOME/.config/BioTK/BioTK.yml``
- ``/etc/BioTK/BioTK.yml``
- ``/opt/BioTK/BioTK.yml``

If none of these are found, the system will use the default settings. If your
custom configuration omits a parameter, then the default will be used.

Configuration options
---------------------

TODO
