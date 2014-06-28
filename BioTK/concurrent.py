from BioTK.cache import CACHE

# See: http://www.davidverhasselt.com/2011/08/06/a-distributed-mutex-and-semaphore-using-redis/

class Semaphore(object):
    def __init__(self, key, size=1):
        assert size >= 1
        self.key = key
        self.token = None
        self.size = size
        if CACHE.getset(key+"_size", size) != size:
            for i in range(size):
                CACHE.lpush(self.key, str(i))
    
    def __del__(self):
        if self.token is not None:
            self.release()

    def acquire(self):
        self.token = int(CACHE.blpop([self.key])[1])

    def release(self):
        assert self.token is not None
        CACHE.lpush(self.key, str(self.token))
        self.token = None
