from .util import *

def get_node_by(label, key, value):
    ix = node_index(label)
    return ix.get(key, value)

def get_single_node_by(label, key, value, strict=False):
    records = get_node_by(label, key, value)
    if strict:
        if len(records) != 1:
            raise Exception("Wanted exactly one record, but %s were returned" \
                    % len(records))
    if len(records):
        return records[0]

def query_node(label, query, ft=False):
    ix = node_index(label, full_text=ft)
    return ix.query(query)

def gene_search(query, taxon_id, exact=False):
    if not exact:
        query = "*" + query + "*"
    q = """
        MATCH (t:`taxon`)-[:taxon]-(g:`gene`) 
        WHERE t.taxon_id={taxon_id}
        AND (g.symbol = "{query}") OR (g.name = "{query}")
        RETURN g
        """.format(query=query, taxon_id=taxon_id)
    #query_node("gene", 'symbol:"%s" OR name:"%s"' % q)
    return get_cypher().execute(q)

def nodes_with_label(label):
    return get_cypher()\
            .execute("""MATCH (n:`{label}`) RETURN n"""\
                .format(label=label))

if __name__ == "__main__":
    #print(get_single_node_by("publication", "pubmed_id", 14890828))
    
    it = query_node("gene", 'name:"*interleukin*"')#, ft=True)
    #it = gene_search("TP53", 9606, exact=True)
    print(next(it))
    #i = 0
    #for item in it:
    #    i += 1
    #print(i)
