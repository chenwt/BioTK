from .util import *

###############
# Manual labels
###############

@populates(check_query="""
SELECT * FROM term_channel
INNER JOIN source
ON term_channel.source_id=source.id
WHERE source.name='URSA'
LIMIT 1;""")
def load_ursa():
    url = "http://ursa.princeton.edu/supp/manual_annotations_ursa.csv"
    path = download(url)
    evidence = "manual"
    evidence_id = ensure_inserted_and_get_index(
            "evidence","name",[evidence])[evidence]
    source = "URSA"
    source_id = ensure_inserted_and_get_index(
            "source", "name", [source])[source]

    sample_accession_to_id = mapq("SELECT accession,id FROM sample;")
    term_name_to_id = mapq("""
            SELECT term.name,term.id FROM term
            INNER JOIN ontology
            ON term.ontology_id=ontology.id
            WHERE ontology.prefix='BTO';""")

    def generate():
        with open(path) as h:
            next(h)
            for line in h:
                gsm, _, bto_name = line.strip().split("\t")
                term_id = term_name_to_id.get(bto_name)
                sample_id = sample_accession_to_id.get(gsm)
                if (term_id is not None) and (sample_id is not None):
                    yield term_id,sample_id,1,evidence_id,source_id

    bulk_load_generator(generate(), "term_channel",
            "term_id","sample_id","channel","evidence_id","source_id")

############
# Text-based
############

def sample_text():
    cursor.execute("""SELECT * FROM channel_text;""")
    for row in cursor:
        yield row

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

@populates(check_query="""
SELECT * FROM term_channel
INNER JOIN term
ON term_channel.term_id=term.id
WHERE term.name='age'
LIMIT 1;""")
def load_channel_age():
    cursor.execute("SELECT id FROM term WHERE name='age';")
    age_term_id = next(cursor)[0]
    rows = []
    evidence = "text mining"
    evidence_id = ensure_inserted_and_get_index(
            "evidence","name",[evidence])[evidence]
    source = "Wren Lab"
    source_id = ensure_inserted_and_get_index(
            "source", "name", [source])[source]

    for sample_id,channel,taxon_id,channel_text,sample_text in channel_text():
        text = " ".join([channel_text or "", sample_text or ""]).strip()
        if not text:
            continue
        default_unit = "year" if taxon_id == 9606 else None
        m = re.search(PATTERNS["age"], text)
        if m is None:
            continue
        age = float(m.group("age"))
        age_end = m.group("age_end")
        if age_end:
            #if not use_age_range:
            #    continue
            age = (age + float(age_end)) / 2
        
        unit = group_if_match(PATTERNS["age_unit"], 
                "age_unit", text) \
                or m.group("age_unit2") \
                or m.group("age_unit1")
                #or default_unit
        if not unit:
            continue
        unit = unit.rstrip("s")
        if not unit in TIME_CONVERSION:
            continue
        conversion_factor = TIME_CONVERSION[unit]
        rows.append((age_term_id, sample_id, channel, evidence_id, source_id,
                age * conversion_factor))
    bulk_load_generator(rows, "term_channel",
            "term_id","sample_id","channel","evidence_id","source_id","value") 

def load():
    load_ursa()
    #load_channel_age()
