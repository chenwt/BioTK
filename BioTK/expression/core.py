__all__ = ["ExpressionSet"]

class ExpressionSet(object):
    """
    Abstract interface for a set of expression data, including 
    sample and feature metadata.
    """
    def expression(self):
       raise NotImplementedError

    def feature_attributes(self):
        raise NotImplementedError

    def sample_attributes(self):
        raise NotImplementedError
