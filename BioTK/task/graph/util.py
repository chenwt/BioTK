import io
import functools

from py2neo import cypher, neo4j, node, rel
import pandas as pd

from BioTK import LOG
from BioTK.cache import CACHE
from BioTK.concurrent import Semaphore

from . import get_graph, get_cypher

#################
# General helpers
#################

def with_graph(fn):
    graph = get_graph()
    return functools.wraps(fn)(functools.partial(fn, graph))

def read_dmp(handle, columns):
    """
    Read a NCBI .dmp file into a DataFrame.
    """
    buffer = io.StringIO()
    for i,line in enumerate(handle):
        buffer.write(line.rstrip("\t|\n") + "\n")
    buffer.seek(0)
    return pd.read_table(buffer, delimiter="\t\|\t", 
            names=columns,
            header=None)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def label_exists(label):
    q = "MATCH (n:`%s`) RETURN n LIMIT 1;" % label
    return len(get_cypher().execute(q)) > 0

def index_nodes_by_property(label, key):
    q = "MATCH (n:`%s`) RETURN n.%s,n;" % (label, key)
    return dict((k,v) for (k,v) in get_cypher().execute(q) if k is not None)

def sanitize_string(s):
    return s.replace("\x00", "")

@with_graph
def node_index(g, label, full_text=False):
    kwargs = {}
    if full_text:
        kwargs["config"] = {"type":"fulltext", "provider":"lucene"}
    return g.get_or_create_index(neo4j.Node, label, **kwargs)

class NodeCache(object):
    def __init__(self, label, prop, lazy=True):
        self.label = label
        self.prop = prop
        self.cache = {}
        self.fetched = False
        if not lazy:
            self.fetch_all()

    def fetch_all(self):
        if not self.fetched:
            self.cache = index_nodes_by_property(self.label, self.prop)
            self.fetched = True

    def items(self):
        return self.cache.items()

    def get(self, key):
        if not key in self.cache:
            search_key = '"%s"' % key if isinstance(key, str) else key
            q = "MATCH (n:`%s`) WHERE n.%s=%s RETURN n LIMIT 1;" % (self.label, self.prop, search_key)
            rs = get_cypher().execute(q)
            self.cache[key] = rs[0].values[0] if len(rs) else None
        return self.cache[key]

class BatchProxy(object):
    """
    Use this object just like a regular batch object, except it
    submits a job every `capacity` operations.

    This is useful because the neo server can time out on very large
    inserts, and removes the necessity of chunking the inserts.
    """

    LOCK_NAME = "BatchProxy"

    def __init__(self, graph=None, capacity=5000, lock_size=1):
        assert capacity > 0
        self.graph = graph or get_graph()
        self.batch = neo4j.WriteBatch(self.graph)
        self.pending = self.total = 0
        self.capacity = capacity
        assert lock_size >= 1
        if lock_size == 1:
            self.lock = CACHE.lock(self.LOCK_NAME)
        else:
            self.lock = Semaphore(self.LOCK_NAME, size=lock_size)
    
    def __del__(self):
        self.run()

    def run(self):
        if self.pending > 0:
            self.lock.acquire()
            self.batch.run()
            self.lock.release()
            self.pending = 0
            self.batch = neo4j.WriteBatch(self.graph)

    def increment(self):
        self.pending += 1
        self.total += 1

    def checkpoint(self):
        if self.pending > self.capacity:
            self.run()

    # Proxied functions

    def add_to_index(self, *args, **kwargs):
        result = self.batch.add_to_index(*args, **kwargs)
        self.increment()
        return result

    def create(self, *args, **kwargs):
        result = self.batch.create(*args, **kwargs)
        self.increment()
        return result

    def add_labels(self, *args, **kwargs):
        result = self.batch.add_labels(*args, **kwargs)
        self.increment()
        return result
    
    # Non-standard convenience functions

    def create_node(self, labels=None, **kwargs):
        kwargs = dict((k,v) for (k,v) in kwargs.items() if v is not None)
        n = self.create(node(**kwargs))
        if labels is not None:
            self.add_labels(n, *labels)
        return n

    def create_relation(self, n1, rtype, n2, **kwargs):
        if (n1 is not None) and (n2 is not None):
            r = self.create(rel(n1, rtype, n2, **kwargs))
            return r
 
