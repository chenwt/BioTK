from . import *
from .query import *

PATTERNS = {
    "age": "[^\w]age( *\((?P<age_unit1>[a-z]*)\))?:\
[ \t]*(?P<age>\d+[\.0-9]*)(( *\- *| (to|or) )\
(?P<age_end>\d+[\.\d]*))?([ \t]*(?P<age_unit2>[a-z]+))?",
    "age_unit": "(age\s*unit[s]*|unit[s]* of age): (?P<age_unit>[a-z])",
    # Tissue (TODO: map to BTO)
    "tissue": "(cell type|tissue|organ) *: *(?P<tissue>[A-Za-z0-9\+\- ]+)",
    # Disease states (TODO: map to DO)
    "cancer": "(tumor|tumour|cancer|sarcoma|glioma|leukem|mesothelioma|metastasis|carcinoma|lymphoma|blastoma|nsclc|cll|ptcl)",
    "infection": "infec"
}
PATTERNS = dict((k, re.compile(v)) for k,v in PATTERNS.items())

# A common additional unit is "dpc", which refers to embryos. 
# Currently ignored.
# Some samples are labeled with something like "11 and 14 weeks". 
# I have no idea what this means, so it's ignored. 
TIME_CONVERSION = {
        "year": 12,
        "y": 12,
        "yr": 12,
        "month": 1,
        "moth": 1, # yes...
        "mo": 1,
        "m": 1,
        "week": 1 / 4.5,
        "wek": 1 / 4.5, # ...
        "wk": 1 / 4.5,
        "w": 1 / 4.5,
        "day": 1 / 30,
        "d": 1 / 30,
        "hour": 1 / (24 * 30),
        "hr": 1 / (24 * 30),
        "h": 1 / (24 * 30)
}

def sample_text(n):
    pass

@QUEUE.task
def sample_age():
    q = "MATCH (s:`sample`)-[r]-(t:`term` {accession:)"LL
    get_cypher().execute(
    for n in nodes_with_label("sample"):
        if not n.get("gsm"):
            continue


