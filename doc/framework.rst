==========================
Data integration framework
==========================

Installation and configuration
==============================

First, install BioTK and all required dependencies via pip.

Next, you will need to install and start services for:

- neo4j server
- redis
- (optionally) RabbitMQ

They can be either on the same or a different machine from the machine
you plan to run BioTK on.

Configure the URIs for these services using the BioTK config file. An example
config file is found in resources/cfg/default.cfg from the root of the BioTK
source tree.

Also in the config file are options and file system paths for optional data
components, like MEDLINE. Set the options appropriately to your use case.
