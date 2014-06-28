"""
Neo4j REST client.

Dependencies:
- redis
"""

class NodeCache(object):
    def __init__(self, host="localhost", port=6379, db=0, prefix="neo.cache"):
        self.db = redis.StrictRedis(host=host, port=port, db=0)

    def get(self, label, key, value):
        pass 
