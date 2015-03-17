"""
"""
# TODO: if tissue maps to a term like "X cell line" and there is a term with different ID "X", 
#  use that and mark cell line status separately

import collections
import re

import networkx as nx

import BioTK.ontology
from BioTK.text import Trie
from BioTK import LOG
from BioTK.data.GEO.metadata import GEOMetaDB

BOUNDARY_CHARACTERS = '\n-._=,:\'; "/|{}()[]<>' \
        + ''.join([str(x) for x in range(0, 10)])

PATTERNS = {
    "age": "[^\w]age( *\((?P<age_unit1>[a-z]*)\))?:\
[ \t]*(?P<age>\d+[\.0-9]*)(( *\- *| (to|or) )\
(?P<age_end>\d+[\.\d]*))?([ \t]*(?P<age_unit2>[a-z]+))?",
    "age_unit": "(age\s*unit[s]*|unit[s]* of age): (?P<age_unit>[a-z])",
    # Tissue (TODO: map to BTO)
    "tissue": "(cell type|tissue|organ) *: *(?P<tissue>[A-Za-z0-9\+\- ]+)",
    # Gender
    "gender": "(gender|sex) *: *(?P<gender>[A-Za-z]+)",
    # Disease states (TODO: map to DO)
    "cancer": "(tumor|tumour|cancer|sarcoma|glioma|leukem|mesothelioma|metastasis|carcinoma|lymphoma|blastoma|nsclc|cll|ptcl)",
    "control": "(control|normal|untreated)",
    "infection": "infec"
}
PATTERNS = dict((k, re.compile(v)) for k,v in PATTERNS.items())

# A common additional unit is "dpc", which refers to embryos. 
# Currently ignored.
# Some samples are labeled with something like "11 and 14 weeks". 
# I have no idea what this means, so it's ignored. 
TIME = {
        "year": 12,
        "y": 12,
        "yr": 12,
        "yrs": 12,
        "month": 1,
        "moth": 1,
        "mon": 1,
        "mo": 1,
        "m": 1,
        "week": 1 / 4.5,
        "wek": 1 / 4.5,
        "wk": 1 / 4.5,
        "w": 1 / 4.5,
        "day": 1 / 30,
        "d": 1 / 30,
        "hour": 1 / (24 * 30),
        "hr": 1 / (24 * 30),
        "h": 1 / (24 * 30)
}

AGE_MAX = {
        "Homo sapiens": 120 * 12,
        "Mus musculus": 5 * 12,
        "Rattus norvegicus": 5 * 12
}

AGE_DEFAULT_UNIT = {
        "Homo sapiens": 12
}

GENDER = {
        "male": "M",
        "m": "M",
        "man": "M",
        "men": "M",
        "mal": "M",
        "boy": "M",
        "woman": "F",
        "women": "F",
        "female": "F",
        "f": "F",
        "fe": "M",
        "girl": "F",
}

GENDER_CODE = {
        "M": 1, "F": 0
}

def _search(pname, text, group=None):
    group = group or pname
    m = re.search(PATTERNS[pname], text)
    if m is not None:
        return m.group(group)

def _expand_synonym(text):
    o = set()
    o.add(text)
    if not text.endswith("s"):
        o.add(text+"s")
    words = text.split()
    if words[-1] == "cell":
        for s in _expand_synonym(" ".join(words[:-1])):
            o.add(s)
    #if text.endswith("cell line"):
    #    for s in _expand_synonym(text.rstrip(" cell line")):
    #        if s not in ["primary"]:
    #            o.add(s)
    return set([s for s in o if len(s) > 3])

def _is_disease_synonym(synonym):
    return any(w.endswith("oma") for w in synonym.split()) \
        or any(w.endswith("emia") for w in synonym.split()) \
        or any(w.endswith("plasia") for w in synonym.split()) \
        or "cancer" in synonym

def _is_invalid_term(synonym):
    invalid = ["culture condition", "infect"]
    return any(x in synonym for x in invalid)

class Annotator(object):
    def __init__(self):
        self.tries = {}
        self.ontologies = {}
        self.graphs = {}

        self.ontologies["BTO"] = BioTK.ontology.fetch("BTO")
        self.graphs["BTO"] = self.ontologies["BTO"].to_graph()

        self.tries["BTO"] = Trie(case_sensitive=False, 
                allow_overlaps=False, 
                boundary_characters=" \t\n")
        for id, synonyms in self._tissue_synonyms().items():
            for s in synonyms:
                self.tries["BTO"].add(s, key=id)
        self.tries["BTO"].build()

        self._age_unit_text = set()

    def _tissue_synonyms(self):
        o = self.ontologies["BTO"]
        g = self.graphs["BTO"]
        depths = dict([(k,g.node[k].get("depth")) for k in g.nodes() if g.node[k].get("depth")])
        synonyms = collections.defaultdict(set)
        canonical = set(o.terms["Name"]) | set(o.synonyms["Synonym"])

        for id,name in zip(o.terms.index, o.terms["Name"]):
            if len(name) > 4:
                synonyms[id].add(name)
            synonyms[id] = synonyms[id] | set(s for s in _expand_synonym(name) if not s in canonical)
        for id,synonym in zip(o.synonyms.index, o.synonyms["Synonym"]):
            if len(synonym) > 4:
                synonyms[id].add(synonym)
            synonyms[id] = synonyms[id] | set(s for s in _expand_synonym(synonym) if not s in canonical)

        diseased = set()
        for id,ss in synonyms.items():
            if any(map(_is_disease_synonym, ss)):
                diseased.add(id)

        synonyms_o = collections.defaultdict(set)
        for id,ss in synonyms.items():
            if any(map(_is_invalid_term, ss)):
                continue
            try:
                path = nx.shortest_path(g, id, g.root)
            except nx.NetworkXNoPath:
                continue
            if id in diseased:
                for parent in path[1:]:
                    if parent in diseased:
                        id = parent
                        continue
                    #if g.edge[id][parent]["type"] != "develops_from":
                    #        break
                    #else:
                    #    id = parent
            synonyms_o[id] = synonyms_o[id] | ss
        return synonyms_o

    def extract_tissue(self, record):
        cell_line = False
        g = self.graphs["BTO"]
        tissue = None
        ms = self.tries["BTO"].search(record.text)
        if ms:
            # TODO: best way? deepest match, longest?
            ms.sort(key=lambda x: -g.node[x.key].get("depth", 0))
            #ms.sort(key=lambda x: x.start - x.end)
            m = ms[0]
            tissue = m.key
            text = record.text[m.start:m.end]
            if text.endswith("cell line"):
                cell_line = True
                ms = self.tries["BTO"].search(text.rstrip(" cell line"))
                if ms is not None and len(ms) == 1:
                    tissue = ms[0].key
        return tissue

    def extract_control(self, record):
        return bool(re.search(PATTERNS["control"], record.text.lower()))

    def extract_gender(self, record):
        text = record.text.lower()
        gender = GENDER_CODE.get(GENDER.get(_search("gender", text, "gender")))
        if record.characteristics and gender is None:
            #ch = "".join([s.title, s.characteristics]).lower()
            ch = record.characteristics.lower()
            f = bool(re.search(r"\bfemale\b", ch))
            m = bool(re.search(r"\bmale\b", ch))
            if f != m:
                if f:
                    gender = GENDER_CODE["F"]
                else:
                    gender = GENDER_CODE["M"]
        return gender

    def extract_age(self, record):
        # FIXME: incorporate age_end
        age = None
        text = record.text.lower()
        m = re.search(PATTERNS["age"], text)
        if m is None:
            return

        unit_text = m.group("age_unit1") or m.group("age_unit2")
        if unit_text is not None:
            self._age_unit_text.add(unit_text)

        if unit_text in ("packyears",):
            return
        unit = TIME.get(unit_text)

        if unit is None:
            if s.organism == "Homo sapiens":
                unit = 12

        age = float(m.group("age"))
        if m.group("age_end"):
            #FIXME: include these?
            #age = (age + float(m.group("age_end"))) / 2
            age = None
        else:
            age *= unit

        # Remove ages too big
        # NB: This could also be done by postprocessing and fitting a per-species 
        # gompertz curve and cutting off at a probability OR determining max 
        # likelihood unit if absent
        if age:
            max_age = AGE_MAX.get(s.organism, 1e10)
            if age >= max_age:
                age = None
        return age 

    def extract_pooled(self, record):
        text = record.text.lower()
        return True if bool(re.search(r"\bpool(ed)?\b", text)) else False

    def extract(self, record):
        pass

if __name__ == "__main__":
    a = Annotator()
    db = GEOMetaDB()

    experiment_tissue = {}
    for e in db.experiments:
        tissue = a.extract_tissue(e)
        if tissue:
            experiment_tissue[e.accession] = tissue

    print("Sample ID", "Platform", "Tissue", "Gender", "Age", "Pool", "Control", sep="\t")
    for s in db.samples:
        accession = "%s-%s" % (s.accession, s.channel)
        tissue = a.extract_tissue(s) or experiment_tissue.get(s.accession) or ""
        pooled = int(a.extract_pooled(s))
        control = int(a.extract_control(s))
        gender = a.extract_gender(s)
        gender = "" if gender is None else gender
        age = a.extract_age(s) or ""
        # TODO: implement
        #cell_line = ""
        row = [tissue, gender, age, pooled, control]

        if any(row[:-2]):
            print(accession, s.platform, *row, sep="\t")

    import sys
    print(a._age_unit_text, file=sys.stderr)
