import yaml

from .util import *

#########
# Loaders
#########

@populates("taxon")
def load_taxon():
    cfg = yaml.load(open("BioTK.yml"))
    taxa = set(cfg["taxa"])
    url = "ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz"
    cached_path = download(url)
    with tarfile.open(cached_path, mode="r:gz") as archive:
        h = io.TextIOWrapper(archive.extractfile("names.dmp"),
                encoding="utf-8")
        columns = ["id", "name", "_", "type"]
        data = read_dmp(h, columns)
        data = data.ix[data["type"] == \
                "scientific name",["id","name"]]
        data = data.drop_duplicates("id").dropna()
        data = data[data["name"].isin(taxa)]
        bulk_load_generator(((int(id), str(name))
                for id, name in
                data.to_records(index=False)),
                "taxon", "id", "name")

@populates("gene")
def load_gene():
    cursor.execute("SELECT id FROM taxon;")
    taxa = set([r[0] for r in cursor])

    url = "ftp://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz"
    path = download(url)
    with tempfile.NamedTemporaryFile("wt") as o:
        nullable = lambda x: None if x == "-" else x
        with io.TextIOWrapper(gzip.open(path, "r"), encoding="utf-8") as h:
            next(h)
            for line in h:
                fields = line.split("\t")
                taxon_id = int(fields[0])
                if taxon_id not in taxa:
                    continue
                gene_id = int(fields[1])
                symbol = nullable(fields[2])
                name = nullable(fields[11])
                row = list(map(str, (taxon_id, gene_id, symbol, name)))
                o.write("\t".join(row) + "\n")
        o.flush()
        bulk_load(o.name, "gene", "taxon_id", "id", "symbol", "name")

def load():
    load_taxon()
    load_gene()
