import pickle

from .io import generic_open as gopen

class Pickleable(object):
    def save(self, f):
        with gopen(f, mode="wb") as h:
            pickle.dump(self, h)

    @staticmethod
    def load(self, f):
        from .io import generic_open as gopen
        with gopen(f, mode="rb") as h:
            return pickle.load(h)

class Closing(object):
    """
    Inherit from this mixin class to make a file-like
    object close upon exiting a 'with statement' block.

    Basically does the same thing as :py:func:`contextlib.closing`.
    """

    def __enter__(self):
        return self

    def __exit__(self, *args):
        try:
            self.close()
        except:
            pass
    
    def close(self):
        raise NotImplementedError
