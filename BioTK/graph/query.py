def gene_search(q):
    """
    Search for genes matching a query string, which might be
    the accession, or a name or synonym.
    """
    gene_ix = node_index("gene")
    try:
        gene_id = int(q)
        return gene_ix.get("gene_id", gene_id)
    except Exception:
        pass
    o = gene_ix.get("symbol", q)
    if o:
        return o

if __name__ == "__main__":
    gene_id = 7157
    term_accession = "GO:0006915"
    print(gene_search("TP53"))
