import multiprocessing as mp

from BioTK.task.graph.load import *

if __name__ == "__main__":
    #(load_taxon.si() | load_gene.si()).apply_async()
    #(load_journal.s() | load_publication.si()).apply_async()
    #load_publication.delay()
    #(load_platform.si() | load_series.si() | load_sample.si()).apply_async()
    #(load_ontology.si() | load_term.si() | load_term_term.si() | load_term_synonym.si()).apply_async()
    load_term.apply_async()
