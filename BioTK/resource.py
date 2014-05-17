import BioTK

RESOURCE_DIR = os.path.abspath(os.path.join(os.path.dirname(BioTK.__file__),
        "..", "resources"))

def path(relpath):
    """
    Get an absolute path to a data resource that comes packaged with BioTK.
    """
    return os.path.join(RESOURCE_DIR, relpath)

def handle(relpath):
    """
    Get a file handle to a data resource that comes packaged with BioTK.
    """
    return open(path(relpath))
