from .util import *
from BioTK.io.GEO import *


def _upsert_platform(p, source_id):
    cursor.execute("""
        SELECT id FROM platform 
        WHERE accession=%s;""", (p.accession,))
    try:
        id = next(cursor)[0]
        cursor.execute("""
            SELECT accession
            FROM probe
            WHERE platform_id=%s
            ORDER BY accession;""", (id,))
        probes = [r[0] for r in cursor]
    except StopIteration:
        cursor.execute("""
            INSERT INTO platform
                (source_id, accession, title, manufacturer)
                VALUES (%s,%s,%s,%s)
            RETURNING id;""", 
            (source_id, p.accession, p.title, p.manufacturer))
        id = next(cursor)[0]
        probes = list(sorted(set(map(str,p.table.index))))
        cursor.executemany("""
            INSERT INTO probe
                (platform_id, accession)
            VALUES (%s,%s)""", ((id,a) for a in probes))
    return id, probes

def _insert_args(table, args, return_id=True):
    q = """INSERT INTO %s VALUES (%s)""" % \
            (table, ", ".join(["%s" for _ in args]))
    if return_id:
        q += "\nRETURNING id;"
    cursor.execute(q, args)
    if return_id:
        return next(cursor)[0]

def _insert_series(s, source_id):
    cursor.execute("""
        INSERT INTO series
            (source_id, pubmed_id, accession, title, summary,
                "type", design, submission_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id;""",
        (source_id, s.pubmed_id, s.accession, s.title, s.summary,
            s.type, s.design, s.submission_date))
    return next(cursor)[0]

def _insert_sample(s, platform_id, probes):
    cursor.execute("""
        SELECT id FROM sample
        WHERE accession=%s LIMIT 1;""", (s.accession,))
    try:
        return next(cursor)[0]
    except StopIteration:
        pass
    sf = s.supplementary_file
    supplementary_file = sf.split("\n") if sf and sf != "NONE" else None
    cursor.execute("""
        INSERT INTO sample
            (platform_id, accession, title, description,
            status, submission_date, last_update_date,
            "type", hybridization_protocol,
            data_processing, contact, supplementary_file,
            channel_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING ID;""", 
            (platform_id, s.accession, s.title, s.description,
            s.status, s.submission_date, s.last_update_date,
            s.type, s.hybridization_protocol, s.data_processing,
            s.contact, supplementary_file, s.channel_count))
    id = next(cursor)[0]
    
    s.table.index = list(map(str, s.table.index))
    for c in s.channels:
        if s.table.dtypes[0] == np.float64:
            data = s.table.iloc[:,0][probes].tolist()
        else:
            data = None
        _insert_args("channel",
                (id, c.channel, c.taxon_id, c.source_name,
                    c.characteristics, c.molecule, c.label,
                    c.treatment_protocol, c.extract_protocol,
                    c.label_protocol, data, None),
                return_id=False)
        break

def load_series(path):
    source = "Gene Expression Omnibus"
    source_id = ensure_inserted_and_get_index("source", "name", 
            [source])[source]
    accession = path.split("/")[-1].split("_")[0]
    LOG.debug("Loading %s" % accession)

    cursor.execute("SELECT id FROM taxon;")
    taxa = set(r[0] for r in cursor)

    platform_accession_to_id = {}
    series_accession_to_id = {}
    probes = {}

    for e in parse(path):
        if isinstance(e, Database):
            continue
        elif isinstance(e, Platform):
            platform_id, p_probes = _upsert_platform(e, source_id)
            probes[platform_id] = p_probes
            platform_accession_to_id[e.accession] = platform_id
        elif isinstance(e, Series):
            series_accession_to_id[e.accession] = _insert_series(e, source_id)
        elif isinstance(e, Sample):
            platform_id = platform_accession_to_id[e.platform_accession]
            if e.taxon_id in taxa:
                sample_id = _insert_sample(e, platform_id, probes[platform_id])

    connection.commit()

@populates("platform")
def load_platform1():
    geo_db = geo_connect()
    gc = geo_db.cursor()

    source = "Gene Expression Omnibus"
    source_id = ensure_inserted_and_get_index("source", "name", 
            [source])[source]

    gc.execute("SELECT %s,gpl,title,manufacturer FROM gpl;" % source_id)
    for r in gc:
        cursor.execute("""
            INSERT INTO platform (source_id,accession,title,manufacturer) 
            VALUES (%s,%s,%s,%s)
            RETURNING id;""", r)

@populates("series")
def load_series1():
    geo_db = geo_connect()
    gc = geo_db.cursor()
    source = "Gene Expression Omnibus"
    source_id = ensure_inserted_and_get_index("source", "name", 
            [source])[source]
    gc.execute("""
        SELECT gse,%s,type,summary,overall_design,submission_date,title 
        FROM gse;""" % source_id)
    bulk_load_generator(gc, "series", "accession", "source_id",
        "type", "summary", "design", "submission_date", "title")

@populates("sample")
def load_sample():
    gpl_to_id = mapq("SELECT accession,id FROM platform;")

    geo_db = geo_connect()
    gc = geo_db.cursor()
    gc.execute("""
        SELECT gpl,gsm,title,status,submission_date,last_update_date,
            type,hyb_protocol,description,data_processing,
            contact,supplementary_file,channel_count
        FROM gsm;""")
    def generate():
        for row in gc:
            row = list(row)
            row[0] = gpl_to_id.get(row[0])
            if not row[0]:
                continue
            row[-1] = int(row[-1])
            yield row
    bulk_load_generator(generate(), "sample", 
            "platform_id", "accession", "title", "status", 
            "submission_date", "last_update_date", 
            "type", "hybridization_protocol", "description",
            "data_processing", "contact", "supplementary_file",
            "channel_count")

@populates("sample_series")
def load_sample_series():
    geo_db = geo_connect()
    gc = geo_db.cursor()
    gsm_to_id = mapq("SELECT accession,id FROM sample;")
    gse_to_id = mapq("SELECT accession,id FROM series;")
    gc.execute("""
        SELECT gse_gsm.gsm,gse
        FROM gse_gsm
        INNER JOIN gsm
        ON gsm.gsm=gse_gsm.gsm;""")
    def generate():
        for gsm,gse in gc:
            sample_id = gsm_to_id.get(gsm)
            series_id = gse_to_id.get(gse)
            if sample_id and series_id:
                yield (gsm_to_id[gsm],gse_to_id[gse])
    bulk_load_generator(generate(), "sample_series",
            "sample_id", "series_id")

@populates("channel")
def load_channel():
    taxon_to_id = mapq("SELECT name,id FROM taxon;")
    gsm_to_id = mapq("SELECT accession,id FROM sample;")
    geo_db = geo_connect()
    gc = geo_db.cursor()
    
    def generate():
        for ch in [1,2]:
            q = """
                SELECT gsm,{n},organism_ch{n},source_name_ch{n},
                    characteristics_ch{n},molecule_ch{n},
                    label_ch{n}, treatment_protocol_ch{n},
                    extract_protocol_ch{n},label_protocol_ch{n}
                FROM gsm
                WHERE channel_count >= {n};""".format(n=ch)
            gc.execute(q)
            for row in gc:
                row = list(row)
                row[0] = gsm_to_id.get(row[0])
                row[2] = taxon_to_id.get(row[2])
                if row[0] is None or row[2] is None:
                    continue
                yield row
    bulk_load_generator(generate(), "channel",
            "sample_id", "channel", "taxon_id",
            "source_name", "characteristics", "molecule",
            "label", "treatment_protocol",
            "extract_protocol", "label_protocol")
 
#######################
# Probe data & mappings
#######################

def read_ailun():
    platform_accession_to_id = mapq("SELECT accession,id FROM platform;")

    for i,path in enumerate(os.listdir(AILUN_DIR)):
        if not path.endswith(".annot.gz"):
            continue
        platform_accession = path.split(".")[0]
        platform_id = platform_accession_to_id.get(platform_accession)
        if not platform_id:
            continue
        path = os.path.join(AILUN_DIR, path)
        mappings = []
        with gzip.open(path, "rt") as h:
            for line in h:
                try:
                    probe_name, gene_id, *_ = line.split("\t")
                    gene_id = int(gene_id)
                    mappings.append((probe_name, gene_id))
                except:
                    pass
        LOG.debug("Processing platform %s" % platform_accession)
        yield platform_id, mappings

@QUEUE.task
def load_probe_from_accession(platform_id, platform_accession):
    GPL_DIR = "/data/public/ncbi/geo/gpl/"
    path = os.path.join(GPL_DIR, "%s-tbl-1.txt" % platform_accession)
    if not os.path.exists(path):
        return
    n = 0
    with open(path) as h:
        for line in h:
            n += 1
    if n > 500000:
        return
    def generate():
        with open(path) as h:
            for line in h:
                try:
                    probe_accession = line.split("\t")[0]
                    yield platform_id, probe_accession
                except:
                    pass
    bulk_load_generator(generate(), "probe", "platform_id", "accession")

@QUEUE.task
@populates("probe")
def load_probe():
    cursor.execute("SELECT id,accession FROM platform;")
    group(load_probe_from_accession.s(*r) for r in cursor)()

@cached
def get_genes():
    cursor.execute("SELECT id FROM gene;")
    return set([r[0] for r in cursor])

@QUEUE.task
def load_probe_gene_from_accession(platform_id, platform_accession):
    LOG.debug(platform_accession)
    AILUN_DIR = "/data/public/ncbi/geo/annotation/AILUN"
    path = os.path.join(AILUN_DIR, "%s.annot.gz" % platform_accession)
    if not os.path.exists(path):
        return
    genes = get_genes()
    probe_name_to_id = mapq("""
        SELECT accession,id FROM probe
        WHERE platform_id=%s;""" % platform_id)
    if len(probe_name_to_id) == 0:
        return

    def generate():
        with gzip.open(path, "rt") as h:
            for line in h:
                try:
                    probe_name, gene_id, *_ = line.split("\t")
                except Exception as e:
                    pass
                gene_id = int(gene_id)
                if not gene_id in genes:
                    continue
                probe_id = probe_name_to_id.get(probe_name)
                if probe_id is None:
                    continue
                yield probe_id, gene_id
    bulk_load_generator(generate(), 
            "probe_gene", "probe_id", "gene_id")

@populates("probe_gene")
def load_probe_gene():
    ensure_index("probe", ["platform_id"])
    ensure_index("sample", ["platform_id"])
    cursor.execute("SELECT id,accession FROM platform;")
    genes = get_genes()
    jobs = list(cursor)
    group(load_probe_gene_from_accession.s(*r) for r in jobs)()

@QUEUE.task
def load_probe_data_from_archive(path):
    platform_accession = os.path.basename(path).split(".")[0]
    LOG.debug(platform_accession)
    cursor.execute("""
        SELECT probe.accession
        FROM probe
        INNER JOIN platform
        ON platform.id=probe.platform_id
        WHERE platform.accession=%s
        ORDER BY probe.id;""", (platform_accession,))
    try:
        probes = [r[0] for r in cursor]
    except Exception as e:
        print(e)
        return
    if len(probes) == 0:
        return
    probes = dict((a,i) for (i,a) in enumerate(probes))

    sample_accession_to_id = mapq("""
        SELECT sample.accession,sample.id
        FROM sample
        INNER JOIN platform
        ON sample.platform_id=platform.id
        WHERE platform.accession='%s';""" % (platform_accession,))

    NaN = float("NaN")
    n = 0
    with tarfile.open(path, "r:xz") as archive:
        for item in archive:
            if not (item.name.startswith("GSM") and \
                    item.name.endswith(".txt")):
                continue
            sample_accession = item.name.split("-")[0]
            sample_id = sample_accession_to_id.get(sample_accession)
            channel = int(item.name.split("-")[-1].rstrip(".txt"))
            if sample_id is None or channel not in [1,2]:
                continue
            with archive.extractfile(item) as h:
                data = np.zeros(len(probes))
                data[:] = np.nan
                lines = h.read().decode("utf-8").strip().split("\n")
                for line in lines:
                    try:
                        probe_accession, value, *_ = line.split("\t")
                    except ValueError:
                        continue
                    probe_index = probes.get(probe_accession)
                    if probe_index is None:
                        continue
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                    data[probe_index] = value
                if np.isnan(data).all():
                    continue
                data = [float(x) if not np.isnan(x) else NaN for x in data]
                assert(len(data) == len(probes))
                cursor.execute("""
                    UPDATE channel
                    SET probe_data=%s
                    WHERE sample_id=%s AND channel=%s;
                    """, (data, sample_id, channel))
                n += 1

    LOG.debug("%s - %s datasets loaded" % (platform_accession, n))
    connection.commit()

@QUEUE.task
@populates(check_query="""
SELECT * FROM channel 
WHERE probe_data IS NOT NULL
LIMIT 1;""")
def load_probe_data():
    GEO_DIR = "/data/public/ncbi/geo/miniml"
    paths = [os.path.join(GEO_DIR, name) for name in os.listdir(GEO_DIR)]
    paths.sort(key=os.path.getsize, reverse=True)
    group(load_probe_data_from_archive.s(path) for path in paths)()

@QUEUE.task
def collapse_probe_data_for_platform(platform_id):
    LOG.debug(platform_id)
    cursor.execute("""
        SELECT taxon.id
        FROM taxon
        INNER JOIN channel
        ON channel.taxon_id=taxon.id
        INNER JOIN sample
        ON sample.id=channel.sample_id
        WHERE sample.platform_id=%s
        GROUP BY taxon.id
        ORDER BY count(taxon.id) DESC
        LIMIT 1;""", (platform_id,))
    taxon_id = next(cursor)[0]

    cursor.execute("""
        SELECT id
        FROM probe
        WHERE platform_id=%s
        ORDER BY id;""", (platform_id,))
    probes = [r[0] for r in cursor]

    cursor.execute("""
        SELECT id
        FROM gene
        WHERE taxon_id=%s
        ORDER BY id;""", (taxon_id,))
    genes = [r[0] for r in cursor]

    cursor.execute("""
            SELECT gene_id, probe_id
            FROM probe_gene
            INNER JOIN probe
            ON probe_gene.probe_id=probe.id
            WHERE probe.platform_id=%s
            ORDER BY probe_id;""", (platform_id,))
    annotation = pd.Series(np.nan, index=probes)
    for gene_id, probe_id in cursor:
        annotation.loc[probe_id] = gene_id

    LOG.debug("Mask loaded")

    while True:
        cursor.execute("""
            SELECT sample_id,channel,probe_data
            FROM channel
            INNER JOIN sample
            ON channel.sample_id=sample.id
            WHERE probe_data IS NOT NULL
            AND gene_data IS NULL
            AND channel.taxon_id=%s
            AND sample.platform_id=%s
            LIMIT 100""", 
            (taxon_id, platform_id,))

        rows = []
        for sample_id, channel, data in cursor:
            expression = pd.Series(data, index=probes)\
                    .to_frame("Value").dropna()
            ix = annotation[expression.index]
            mu = expression.groupby(ix).mean().iloc[:,0]
            mu = mu + 1e-5 - mu.min()
            if mu.max() > 100:
                mu = mu.apply(np.log2)
            mu = (mu - mu.mean()) / mu.std()
            data = list(map(float, mu[genes]))
            rows.append((data, sample_id, channel))

        if not rows:
            break
        insert = connection.cursor()
        insert.executemany("""
            UPDATE channel
            SET gene_data=%s
            WHERE channel.sample_id=%s 
            AND channel.channel=%s""",
            rows)
        LOG.debug("Inserting chunk")
        connection.commit()

@populates(check_query="""
    SELECT * FROM channel
    WHERE gene_data IS NOT NULL
    LIMIT 1;""")
def collapse_probe_data():
    cursor.execute("""
        SELECT platform.id
        id FROM platform
        INNER JOIN sample
        ON sample.platform_id=platform.id
        INNER JOIN channel
        ON channel.sample_id=sample.id
        GROUP BY platform.id
        ORDER BY COUNT(channel.channel) DESC;""")
    platforms = [r[0] for r in cursor]
    group(collapse_probe_data_for_platform.s(
        platform_id) for platform_id in platforms)()

def load():
    root = "/data/public/ncbi/geo/series"
    for file in os.listdir(root):
        if file.endswith("_family.soft.gz"):
            path = os.path.join(root, file)
            load_series(path)

    #load_probe()
    #load_probe_gene()
    #load_probe_gene_from_accession(71, "GPL96")
    #load_probe_data()
    #collapse_probe_data()
