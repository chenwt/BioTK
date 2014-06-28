import functools

from py2neo import neo4j, cypher

_graph = None
_cypher = None

def reconnect():
    global _graph, _cypher
    _graph = neo4j.GraphDatabaseService()
    _cypher = cypher.Session()
    return _graph, _cypher

def get_graph():
    global _graph
    if _graph is None:
        _graph, _ = reconnect()
    return _graph

def get_cypher():
    global _cypher
    if _cypher is None:
        _, _cypher = reconnect()
    return _cypher

from .util import *
