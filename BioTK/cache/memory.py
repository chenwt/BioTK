"""
Cache function results in Redis.
"""
__all__ = ["cached", "CACHE"]

import collections
import functools
import pickle

import lz4
import redis

from BioTK import CONFIG

CACHE = None
def initialize_cache():
    global CACHE
    CACHE = redis.StrictRedis(
            host=CONFIG["redis.host"],
            port=int(CONFIG["redis.port"]))

# Set to a long time on the assumption that the memory policy
# is some variant of "volatile-*" 
# (the default, volatile-lru, is probably best)
DEFAULT_EXPIRY = 604800

def cached(fn):
    """
    Memoize the decorated function's arguments in Redis.

    Requirements: 
    - Function args and kwargs must be hashable
    - Function result must be pickleable
    """
    @functools.wraps(fn)
    def decorator(*args, **kwargs):
        if CACHE is None:
            initialize_cache()

        kwargs_tuple = tuple(sorted(kwargs.items()))
        if not isinstance(args, collections.Hashable) \
                or not isinstance(kwargs_tuple, collections.Hashable):
            msg = "Function arguments not hashable:"
            msg += "\n\targs:%s\n\tkwargs:%s"
            raise Exception(msg % (args, kwargs))
        key = "%s.%s[%s]" % (fn.__module__, fn.__name__, 
                hash((args,kwargs_tuple)))
        if not CACHE.exists(key):
            value = fn(*args, **kwargs)
            pickled_value = lz4.dumps(pickle.dumps(value))
            CACHE.setex(key, DEFAULT_EXPIRY, pickled_value)
            return value
        else:
            pickled_value = CACHE.get(key)
            return pickle.loads(lz4.loads(pickled_value))
    return decorator
