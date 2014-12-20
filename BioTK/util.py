from os.path import abspath, dirname, join

def identity(x):
    return x

class ResourceLookup(object):

    def __init__(self, pkgname):
        module = __import__(pkgname)
        self._basedir = abspath(join(dirname(module.__file__), 
            "..", "resources"))

    def path(self, relpath):
        """
        Get an absolute path to a data resource.
        """
        return join(self._basedir, relpath)

    def handle(self, relpath, mode="r"):
        """
        Get a file handle to a data resource.
        """
        return open(self.path(relpath), mode=mode)

def chunks(it, size=1000):
    """
    Divide an iterator into chunks of specified size. A
    chunk size of 0 means no maximum chunk size, and will
    therefore return a single list.
    
    Returns a generator of lists.
    """
    if size == 0:
        yield list(it)
    else:
        chunk = []
        for elem in it:
            chunk.append(elem)
            if len(chunk) == size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk
