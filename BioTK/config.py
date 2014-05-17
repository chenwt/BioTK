"""
Configuration of global options.

First, the defaults are loaded from the default.cfg file that comes
with the distribution. Then, a variety of places are searched for 
user-provided configuration files, which, if found, override the 
defaults.

This module also sets up logging.
"""

__all__ = ["CONFIG", "LOG", "CACHE_DIR"]

import configparser
import logging
import os
import sys

default_cfg_path = os.path.join(os.path.dirname(__file__), "default.cfg")
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

log_formatter = logging.Formatter(CONFIG["log.format"])
LOG.setFormatter(log_formatter)

log_level = CONFIG["log.level"]
try:
    LOG.setLevel(getattr(logging, log_level))
except AttributeError:
    LOG.critical("The configured log level (%s) is invalid. \
See the Python 'logging' module documentation for valid values." % log_level) 
    sys.exit(1)

if CONFIG.getboolean("log.console"):
    # defaults to sys.stderr
    LOG.addHandler(logging.StreamHandler())
if CONFIG.getboolean("log.syslog"):
    LOG.addHandler(logging.handlers.SysLogHandler())
log_file = CONFIG.get("log.file", "").strip()
if log_file:
    LOG.addHandler(logging.FileHandler(log_file))

# Now that logging is set up, notify the user whether custom
# configuration was loaded that might override the defaults
if user_cfg_path is not None:
    LOG.info("User configuration file was loaded from %s" % path)

#################
# Configure cache
#################

CACHE_DIR = CONFIG["cache.dir"]
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

####################
# Configure datasets
####################

# Set data paths to be relative to the data root, if necessary
data_root = os.path.abspath(CONFIG["data.root.dir"])
for key, path in CONFIG.items():
    if key.startswith("data.") and key.endswith(".dir"):
        if not os.path.isabs(path):
            CONFIG[key] = os.path.join(data_root, path)
