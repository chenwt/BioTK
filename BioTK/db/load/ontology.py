from .util import *

def load_ontology(prefix, name, path):
    cursor.execute("""
        INSERT INTO ontology (prefix,name) VALUES (%s,%s) RETURNING id""",
            (prefix, name))
    ontology_id = next(cursor)[0]

    with open(path) as h:
        o = OBO.parse(h)

    # Insert (if necessary) and cache namespaces
    namespace_to_id = ensure_inserted_and_get_index( 
            "namespace", "text", o.terms["Namespace"])
    accession_to_id = {}

    # Insert terms
    for accession, name, namespace in o.terms.to_records(index=True):
        if isinstance(namespace, list) or namespace is None:
            # FIXME
            namespace_id = None
        else:
            namespace_id = namespace_to_id[namespace]
        cursor.execute("""
        INSERT INTO term (ontology_id,namespace_id,accession,name)
        VALUES (%s,%s,%s,%s)
        RETURNING id;
        """, (ontology_id,namespace_id,accession,name))
        accession_to_id[accession] = next(cursor)[0]
                    
    # Insert synonyms
    synonyms = o.synonyms
    synonym_to_id = ensure_inserted_and_get_index(
            "synonym", "text", set(synonyms["Synonym"]))

    # Insert term-synonym links
    for accession, synonym in synonyms.to_records():
        term_id = accession_to_id[accession]
        synonym_id = synonym_to_id[synonym]
        cursor.execute("INSERT INTO term_synonym VALUES (%s,%s)",
                (term_id,synonym_id))
       
    # Insert relationships    
    relationship_to_id = ensure_inserted_and_get_index(
            "relationship", "name", set(o.relations["Relation"]))

    # Insert term-term links
    inserted_terms = set(o.terms.index)
    for agent, target, r in o.relations.to_records(index=False):
        agent_id = accession_to_id.get(agent)
        target_id = accession_to_id.get(target)
        if (agent_id is None) or (target_id is None):
            continue
        relationship_id = relationship_to_id[r]
        cursor.execute("""
        INSERT INTO term_term (agent_id,target_id,relationship_id)
        VALUES (%s,%s,%s);
        """, (agent_id, target_id, relationship_id))

OBO_PATH = "/data/public/ontology/obo/"
ONTOLOGIES = [
        ("GO", "Gene Ontology"),
        ("BTO", "Brenda Tissue Ontology"),
        ("PATO", "Phenotypic Quality Ontology")
]

@populates("ontology", "term")
def load_ontologies():
    for prefix, name in ONTOLOGIES:
        LOG.debug("Loading data for %s (%s)" % (prefix, name))
        load_ontology(prefix, name, OBO_PATH+prefix+".obo")
       
############################################
# Manual or official gene/sample annotations
############################################

@populates(check_query="""
SELECT * FROM term_gene
INNER JOIN source
ON source.id=term_gene.source_id
WHERE source.name='Gene Ontology Consortium'
LIMIT 1;""")
def load_gene_go():
    accession_to_term_id = mapq("select accession,id FROM term")
    source = "Gene Ontology Consortium"
    source_id = ensure_inserted_and_get_index("source","name",
            [source])[source]
    cursor.execute("SELECT id FROM gene;")
    genes = set(row[0] for row in cursor)

    url = "ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz"
    path = download(url)
    with gzip.open(path, "r") as h:
        df = pd.read_table(h, skiprows=1, 
                header=None, names=("Taxon ID", "Gene ID", "Term ID", 
                    "Evidence", "Qualifier", "TermName", "PubMed", "Category"))
        df = df[df["Gene ID"].isin(genes)]
        evidence_to_id = ensure_inserted_and_get_index("evidence","name",
                set(df["Evidence"]))
        records = ((accession_to_term_id[term_accession], int(gene_id),
                evidence_to_id[evidence], source_id)
                for gene_id,term_accession,evidence 
                in df.iloc[:,1:4].dropna().itertuples(index=False))
        bulk_load_generator(records, "term_gene",
                "term_id","gene_id","evidence_id","source_id")

def load():
    load_ontologies()
    load_gene_go()
