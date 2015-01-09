"""
Configuration of global options.

First, the defaults are loaded from the default.cfg file that comes
with the distribution. Then, a variety of places are searched for 
user-provided configuration files, which, if found, override the 
defaults.

This module also sets up logging.
"""

__all__ = ["CONFIG", "LOG", "CACHE_DIR"]

import yaml
import logging
import os
import sys

from BioTK import resource

default_cfg_path = resource.path("cfg/default.yml")
with open(default_cfg_path) as h:
    CONFIG = yaml.load(h)

cfg_search_paths = [
        os.path.join(os.curdir, "BioTK.yml"),
        os.path.expanduser("~/.BioTK.yml"),
        os.path.expanduser("~/.config/BioTK/config.yml"),
        "/etc/BioTK/config.yml",
        "/opt/BioTK/config.yml"
]

user_cfg_path = None
for path in cfg_search_paths:
    if os.path.exists(path):
        with open(path) as h:
            CONFIG.merge(yaml.load(h))
        user_cfg_path = path
        break

################
# Set up logging
################

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format)
LOG = logging.getLogger("BioTK")
LOG.setLevel(CONFIG["log"]["level"])

# Now that logging is set up, notify the user whether custom
# configuration was loaded that might override the defaults
if user_cfg_path is not None:
    LOG.info("User configuration file loaded from '%s'" % path)

######################
# Configure file cache
######################

CACHE_DIR = os.path.expanduser(CONFIG["cache"]["root"])
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)
