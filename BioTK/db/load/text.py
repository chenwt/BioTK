from .util import *

from BioTK.io import MEDLINE

MEDLINE_DIR = "/data/public/ncbi/medline/"

@populates("journal")
def load_journal():
    issn = set()
    nlm_id = set()
    def generate():
        for path in os.listdir(MEDLINE_DIR):
            if not path.endswith(".xml.gz"):
                continue
            path = os.path.join(MEDLINE_DIR, path)
            for article in MEDLINE.parse(path):
                journal = article.journal
                if journal.issn in issn:
                    continue
                if journal.id in nlm_id:
                    continue
                nlm_id.add(journal.id)
                issn.add(journal.issn)
                yield journal.id, journal.name, journal.issn
    bulk_load_generator(generate(), "journal",
            "nlm_id", "name", "issn")

@populates("publication")
def load_publication():
    journal_by_nlm_id = mapq("""
        SELECT nlm_id,id
        FROM journal
        WHERE nlm_id IS NOT NULL;""")
    def generate():
        ids = set()
        for path in os.listdir(MEDLINE_DIR):
            if not path.endswith(".xml.gz"):
                continue
            LOG.debug(path)
            for article in MEDLINE.parse(path):
                journal_id = journal_by_nlm_id.get(article.journal.id)
                if article.id in ids:
                    continue
                ids.add(article.id)
                yield journal_id, article.id, article.title, article.abstract
    bulk_load_generator(generate(), "publication", 
            "journal_id", "pubmed_id", "title", "abstract")

############
# CARPE DIEM
############

@populates(check_query="""
        SELECT * from term_term""")
def carpe_diem():
    pass

def load():
    if os.path.exists(MEDLINE_DIR):
        load_journal()
        load_publication()
