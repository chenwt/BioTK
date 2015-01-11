import os
import sys

from .linalg import *

try:
    from BioTK.version import version as __version__
except ImportError:
    __version__ = "HEAD"

from .util import *
resource = ResourceLookup("BioTK")

from .config import *

import BioTK.data as data
import BioTK.expression as expression
import BioTK.genome as genome
import BioTK.io as io
import BioTK.learn as learn
import BioTK.matrix as matrix
import BioTK.text as text

from .mmat import *

# Don't throw broken pipe error at EOF
from signal import signal, SIGPIPE, SIG_DFL, SIGINT
signal(SIGPIPE,SIG_DFL)
# Don't show traceback on Ctrl-C
signal(SIGINT, lambda x,y: sys.exit(0))
