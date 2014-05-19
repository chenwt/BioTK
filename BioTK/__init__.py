import os

from .linalg import *

try:
    from BioTK.version import version as __version__
except ImportError:
    __version__ = "HEAD"

from BioTK.config import *
