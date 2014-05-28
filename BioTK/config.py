"""
Configuration of global options.

First, the defaults are loaded from the default.cfg file that comes
with the distribution. Then, a variety of places are searched for 
user-provided configuration files, which, if found, override the 
defaults.

This module also sets up logging.
"""

__all__ = ["CONFIG", "TAXA", "LOG", "CACHE_DIR"]

import configparser
import logging
import os
import sys

from BioTK import resource

default_cfg_path = resource.path("cfg/default.cfg")
CONFIG = configparser.ConfigParser()
CONFIG.read(default_cfg_path)

# Add a BIOTK_CONF environment variable?
# Interpret /etc/BioTK relative to an installation directory?

cfg_search_paths = [
        os.path.join(os.curdir, "BioTK.cfg"),
        os.path.expanduser("~/.BioTK.cfg"),
        os.path.expanduser("~/.config/BioTK/BioTK.cfg"),
        "/etc/BioTK/BioTK.cfg"
]

user_cfg_path = None
for path in cfg_search_paths:
    if os.path.exists(path):
        CONFIG.read(path)
        user_cfg_path = path
        break

CONFIG = CONFIG["BioTK"]

################
# Set up logging
################

LOG = logging.getLogger("BioTK")

#log_format = CONFIG["log.format"]
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_formatter = logging.Formatter(log_format)

log_level = CONFIG["log.level"]
try:
    LOG.setLevel(getattr(logging, log_level))
except AttributeError:
    LOG.critical("The configured log level (%s) is invalid. \
See the Python 'logging' module documentation for valid values." % log_level) 
    sys.exit(1)

def add_handler(handler):
    handler.setFormatter(log_formatter)
    LOG.addHandler(handler)

if CONFIG.getboolean("log.console"):
    # defaults to sys.stderr
    add_handler(logging.StreamHandler())
if CONFIG.getboolean("log.syslog"):
    add_handler(logging.handlers.SysLogHandler())
log_file = CONFIG.get("log.file", "").strip()
if log_file:
    add_handler(logging.FileHandler(log_file))

# Now that logging is set up, notify the user whether custom
# configuration was loaded that might override the defaults
if user_cfg_path is not None:
    LOG.info("User configuration file loaded from '%s'" % path)

#################
# Configure cache
#################

CACHE_DIR = os.path.expanduser(CONFIG["cache.dir"])
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

####################
# Configure datasets
####################

def resolve_dir(root, path):
    return path if os.path.isabs(path) else os.path.join(root, path)

# Set data paths to be relative to the data root, if necessary
data_root = CONFIG["data.root.dir"] = os.path.abspath(CONFIG["data.root.dir"])
ncbi_root = CONFIG["ncbi.root.dir"] = \
        resolve_dir(data_root, CONFIG["ncbi.root.dir"])
ucsc_root = CONFIG["ucsc.root.dir"] = \
        resolve_dir(data_root, CONFIG["ucsc.root.dir"])

for key, path in CONFIG.items():
    if key.endswith(".dir") and not "root" in key:
        if key.startswith("ncbi."):
            CONFIG[key] = resolve_dir(ncbi_root, path)

# Read enabled taxa into global variable
# (will this work in a multiprocessing or distributed environment?)
TAXA = list(map(int, CONFIG["data.taxa"].split(",")))
