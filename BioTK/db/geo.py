import re
import os
import sys

from sqlalchemy import create_engine, MetaData, Table, \
        Column, Integer, String, \
        LargeBinary, Float, Boolean
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker, deferred
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import sessionmaker, deferred, relationship, backref

from BioTK.text import Trie

#######################
# Constants and helpers
#######################

def group_if_match(pattern, group, text):
    m = re.search(pattern, text)
    if m:
        return m.group(group)

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

TISSUE_REMOVE = [
       "whole", "peripheral", "primary"
]

TISSUE_MAPPING = [
    ("colorecal", "colon"),
    ("colon", "colon"),
    ("bone marrow", "bone marrow"),
    ("adipose", "adipose"),
    ("skeletal muscle", "skeletal muscle"),
    ("mammary", "breast"),
    ("breast", "breast"),
    ("colorectal", "colon"),
    ("gingival", "gingiva"),
    ("wbc", "leukocyte"),
    ("white blood cell", "leukocyte"),
    ("leukocyte", "leukocyte"),
    ("red blood cell", "erythrocyte"),
    ("blood", "blood"),
    ("pbmc", "blood"),
    ("renal", "kidney"),
    ("kidney", "kidney"),
    ("liver", "liver"),
    ("hepatic", "liver"),
    ("hepatocyte", "liver"),
    ("lung", "lung"),
    ("pneumatic", "lung"),
    ("cardiac", "heart"),
    ("heart", "heart"),
    ("myocard", "heart"),
    ("ca1", "CA1"),
    ("ca2", "CA2"),
    ("ca3", "CA3"),
    ("hippocamp", "hippocampus"),
    ("temporal cortex", "temporal cortex"),
    ("frontal cortex", "frontal cortex"),
    ("occipital", "occipital cortex"),
    ("cerebel", "cerebellum"),
    ("retina", "retina"),
    ("neuron", "neuron"),
    ("brain", "brain"),
    ("spleen", "spleen"),
    ("splenocyte", "spleen"),
    ("thymus", "thymus"),
    ("ovarian", "ovary"),
    ("skin", "skin"),
    ("epidermis", "skin"),
    ("lymph nodes", "lymph node"),
    ("prostate", "prostate"),
    ("pancrea", "pancreas"),
    ("conjuntiva", "conjunctiva"),
    ("thyroid", "thyroid"),
    ("fibroblast", "fibroblast"),
    ("smooth muscle", "smooth muscle"),
    ("t cell", "T cell"),
    ("t-cell", "T cell"),
    ("b cell", "B cell"),
    ("b-cell", "B cell"),
    ("monocyte", "monocyte"),
    ("endothel", "endothelium"), 
    ("blood vessel", "endothelium"),
    ("adrenal", "adrenal gland"),
    ("cervix", "cervix"), # FIXME? aren't there multiple kinds of cervix? 
    ("cerebr", "cerebrum")
]

trie = Trie(case_sensitive=False)
for pattern, tissue in TISSUE_MAPPING:
    trie.add(pattern, key=tissue)
    trie.add(tissue, key=tissue)
trie.build()

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

path = "/dev/shm/GEOmetadb.sqlite"

Base = declarative_base()

engine = create_engine("sqlite:///%s" % path)
Session = sessionmaker(bind=engine)
db = Session()

class Sample(Base):
    __tablename__ = "gsm"
    __table_args__ = (
        {
            "autoload": True,
            "autoload_with": engine
        })

    rowid = Column(Integer, primary_key=True)

    @property
    def id(self):
        return int(self.gsm[3:])

    @property
    def text(self):
        if not hasattr(self, "_text"):
            fields = [self.title, self.description, self.source_name_ch1,
                    self.characteristics_ch1]
            self._text = "\n".join([v if v else "" for v in fields])\
                    .lower()\
                    .replace(";", "\n")\
                    .replace("pnd", "postnatal day")\
                    .replace("postnatal ", "")
        return self._text

    def age(self, default_unit=None, use_age_range=True):
        m = re.search(PATTERNS["age"], self.text)
        if m is None:
            return
        age = float(m.group("age"))
        age_end = m.group("age_end")
        if age_end:
            if not use_age_range:
                return
            age = (age + float(age_end)) / 2
        
        unit = group_if_match(PATTERNS["age_unit"], 
                "age_unit", self.text) \
                or m.group("age_unit2") \
                or m.group("age_unit1") \
                or default_unit
        if not unit:
            return
        unit = unit.rstrip("s")
        if not unit in TIME_CONVERSION:
            return
        conversion_factor = TIME_CONVERSION[unit]
        return age * conversion_factor

    @property
    def tissue(self):
        """
        m = re.search(PATTERNS["tissue"], self.text)
        if m is not None:
            tissue = m.group("tissue")
            for rm in TISSUE_REMOVE:
                tissue = tissue.replace(rm, "")
            for map_from, map_to in TISSUE_MAPPING:
                if map_from in tissue:
                    tissue = map_to
                    break
            return tissue.strip()
        else:
        """
        # FIXME: instead of sorting by length, sort by BTO specificity
        matches = trie.search(self.text)
        if matches:
            matches.sort(key=lambda x: - (x.end - x.start))
            return matches[0].key

    @property
    def disease(self):
        if "control" in self.text:
            return
        if re.search(PATTERNS["cancer"], self.text):
            return "cancer"
        if re.search(PATTERNS["infection"], self.text):
            return "infection"
