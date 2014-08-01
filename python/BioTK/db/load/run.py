import setproctitle

from .util import *

from .core import load as load_core
from .ontology import load as load_ontology
from .annotate import load as load_annotate
from .text import load as load_text
from .geo import load as load_geo

#import BioTK.db.load.core as core
#import BioTK.db.load.ontology as ontology
#from .geo import load
#from .text import load
#from .annotate import load

def load_all():
    setproctitle.setproctitle("btk-db")

    initialize()
    ensure_schema()

    #load_core()
    #load_ontology()
    #load_text()
    #load_geo()
    load_annotate()

    #index_all()
    LOG.info("Load complete")

    #load_probe_data_from_archive("/data/public/ncbi/geo/miniml/GPL96.tar.xz").delay()
    #collapse_probe_data_for_platform(71)

if __name__ == "__main__":
    load_all()
