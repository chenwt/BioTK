import os

from .linalg import *

try:
    from BioTK.version import version as __version__
except ImportError:
    __version__ = "HEAD"

from .util import ResourceLookup
resource = ResourceLookup("BioTK")

from BioTK.config import *

# Don't throw broken pipe error at EOF
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)
