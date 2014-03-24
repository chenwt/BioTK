"""
Simple reader for OBO (Open Biomedical Ontology) files.
"""

import collections

import networkx as nx
import pandas as pd
import numpy as np

Term = collections.namedtuple("Term", [
    "id", "name", "synonym", "is_a", "part_of", "namespace"
])

def _make_term(attrs):
    if ("id" in attrs) and ("name" in attrs):
        for key in Term._fields:
            attrs.setdefault(key, [])
        return Term(**attrs)

def _parse(handle):
    """
    A simple iterative reader for OBO (Open Biomedical Ontology) files.
    
    :param handle: File handle to the OBO file
    :type handle: A file handle in 'rt' mode

    Currently, only a subset of the OBO specification is supported. 
    Namely, only the following attribute of [Term] entries:
    - id
    - name
    - synonym
    - is_a
    - part_of
    - namespace
    """
    is_term = False
    attrs = collections.defaultdict(list)
    for line in handle:
        line = line.strip()
        if line in ("[Term]", "[Typedef]", "[Instance]"):
            is_term = line == "[Term]"
            t = _make_term(attrs)
            if t and is_term: 
                yield t
            attrs = collections.defaultdict(list)
        elif line:
            try:
                key, value = line.split(": ", 1)
            except ValueError:
                continue

            if key == "id":
                attrs["id"] = value
            elif key == "name":
                attrs["name"] = value
            elif key == "is_a":
                attrs["is_a"].append(value.split("!")[0].strip())
            elif key == "part_of":
                attrs["part_of"].append(value.split("!")[0].strip())
            elif key == "namespace":
                attrs["namespace"] = value
            elif key == "synonym":
                value = value[1:]
                attrs["synonym"].append(value[:value.find("\"")])
    t = _make_term(attrs)
    if t and is_term: 
        yield t

def _parse_as_data_frame(handle):
    terms, synonyms, relations = [], [], []

    for t in _parse(handle):
        terms.append((t.id, t.name, t.namespace))
        for s in t.synonym:
            synonyms.append((t.id, s))
        for target in t.is_a:
            relations.append((t.id, target, "is_a"))

    terms = pd.DataFrame.from_records(terms,
            columns=["Term ID", "Name", "Namespace"],
            index="Term ID")
    synonyms = pd.DataFrame.from_records(synonyms,
            columns=["Term ID", "Synonym"],
            index="Term ID")
    relations = pd.DataFrame.from_records(relations,
            columns=["Agent", "Target", "Relation"])
    return terms, synonyms, relations

class Ontology(object):
    def __init__(self, terms, synonyms, relations):
        self._terms = terms
        self._synonyms = synonyms
        self._relations = relations

    @property
    def terms(self):
        return self._terms.copy()

    @property
    def synonyms(self):
        return self._synonyms.copy()

    @property
    def relations(self):
        return self._relations.copy()

    def to_graph(self, relations=["is_a"]):
        """
        Convert this Ontology into a NetworkX graph for efficient traversal.

        Parameters
        ----------
        relations : list of str, optional
            The relation types to use as edges in the graph. (default: is_a)

        Returns
        -------
        A :class:`networkx.DiGraph`. The edges are directed in the 
            same direction as the relation. In the common case of 
            the `is_a` relation, this means from children to parents.
        """
        g = nx.DiGraph()
        R = self.relations.ix[self.relations["Relation"].isin(relations),:]
        for id,name,ns in self.terms.to_records():
            g.add_node(id, name=name, namespace=ns)
        for id,synonym in self.synonyms.to_records():
            if not "synonyms" in g.node[id]:
                g.node[id]["synonyms"] = []
            g.node[id]["synonyms"].append(synonym)
        for _,agent,target,relation in R.to_records():
            g.add_edge(agent, target, type=relation)
        return g

    @property
    def ancestry_table(self):
        g = self.to_graph()
        rows = []
        for n in g.nodes():
            for ancestors in nx.dfs_successors(g, n).values():
                for ancestor in ancestors:
                    rows.append((ancestor, n))
        return pd.DataFrame(rows, columns=["Ancestor", "Descendant"])

    def annotation_matrix(self, mapping, recursive=False):
        """
        Create a DataFrame representing the mapping between a set
        of ontology terms and another set of objects (genes, samples, etc.).

        Parameters
        ----------
        mapping : :class:`pandas.DataFrame`
            A DataFrame representing the mapping between ontology terms 
            and genes/samples/whatever. Two columns are required:
            Column 1 - The sample/gene ID
            Column 2 - The ontology term ID
            Column 3 (optional) - An integer, float, or boolean column. If not 
                provided, an int8 :class:`pandas.DataFrame` will be returned
                wherein all matching sample/ontology pairs will
                be assigned integer value 1 and non-matching pairs will be
                assigned 0.
        recursive : bool, optional
            If True, the ontology tree will be traversed and all parent
            terms will be assigned the same value

        Returns
        -------
        :class:`pandas.DataFrame`
            Rows are sample/gene IDs, columns are ontology IDs, and
            values are ints/floats/booleans as described above.
        """
        assert mapping.shape[1] in (2,3), "Provided DataFrame must have either two or three columns."

        A = mapping
        if A.shape[1] == 2:
            A["Value"] = 1
            dtype = np.uint8
        else:
            dtype = mapping.iloc[2].dtype
            assert dtype is not np.object, "Value column must be numeric or boolean, not object."

        A.columns = [A.columns[0]] + ["Term ID", "Value"]

        if recursive:
            inferred = mapping.merge(self.ancestry_table,
                    left_on=A.columns[1],
                    right_on="Descendant")\
                            .ix[:,["Ancestor", A.columns[0], "Value"]]
            inferred.columns = ["Term ID", A.columns[0], "Value"]
            A = pd.concat([A, inferred], axis=0).drop_duplicates()
        return A.pivot(A.columns[0], "Term ID", "Value")\
                .fillna(0).astype(dtype)

        
def parse(handle):
    return Ontology(*_parse_as_data_frame(handle))
