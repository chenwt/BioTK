-- Datasets

CREATE TABLE IF NOT EXISTS platform (
    source_id INTEGER NOT NULL,

    title VARCHAR,
    manufacturer VARCHAR,

    PRIMARY KEY (id),
    FOREIGN KEY (source_id) REFERENCES source(id)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS series (
    source_id INTEGER NOT NULL,
    --pubmed_id INTEGER,

    accession VARCHAR UNIQUE,

    title VARCHAR,
    summary VARCHAR,
    "type" VARCHAR,
    design VARCHAR,
    submission_date DATE,

    FOREIGN KEY (source_id) REFERENCES source(id)
    --FOREIGN KEY (pubmed_id) REFERENCES publication(pubmed_id)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS sample (
    platform_id INTEGER NOT NULL,

    accession VARCHAR UNIQUE NOT NULL,

    title VARCHAR,
    description VARCHAR,
    status VARCHAR,
    submission_date VARCHAR,
    last_update_date VARCHAR,
    "type" VARCHAR,
    hybridization_protocol VARCHAR,
    data_processing VARCHAR,
    contact VARCHAR,
    supplementary_file VARCHAR[],
    channel_count INTEGER,

    FOREIGN KEY(platform_id) REFERENCES platform(id) ON DELETE CASCADE
) INHERITS (named_entity);

CREATE TABLE IF NOT EXISTS channel (
    sample_id INTEGER NOT NULL,
    channel SMALLINT NOT NULL,

    taxon_id INTEGER NOT NULL,

    source_name VARCHAR,
    characteristics VARCHAR,
    molecule VARCHAR,
    label VARCHAR,
    treatment_protocol VARCHAR,
    extract_protocol VARCHAR,
    label_protocol VARCHAR,

    -- The probes/genes are ordered by ID within the corresponding platform 
    probe_data double precision[],
    gene_data double precision[],

    PRIMARY KEY (sample_id, channel),
    FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE,
    FOREIGN KEY (taxon_id) REFERENCES taxon(id) ON DELETE CASCADE
);

--CREATE OR REPLACE VIEW sample_text AS 
--SELECT * FROM (
--    SELECT id, (title || ' ' || source_name || ' ' 
--        || description || ' ' || characteristics) AS text
--    FROM sample) AS q
--WHERE text IS NOT NULL;

CREATE TABLE IF NOT EXISTS sample_series (
    sample_id INTEGER,
    series_id INTEGER,

    PRIMARY KEY (sample_id, series_id),
    FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
);

-- Probes & probe mappings

CREATE TABLE probe (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER,
    accession VARCHAR,
    data HSTORE,

    UNIQUE (platform_id, accession),

    FOREIGN KEY (platform_id) REFERENCES platform(id) 
        ON DELETE CASCADE
);

CREATE TABLE probe_gene (
    probe_id INTEGER,
    gene_id INTEGER,

    PRIMARY KEY (probe_id, gene_id),
    FOREIGN KEY (probe_id) REFERENCES probe(id) 
        ON DELETE CASCADE,
    FOREIGN KEY (gene_id) REFERENCES gene(id) 
        ON DELETE CASCADE
);

-- Gene and sample annotation

CREATE TABLE IF NOT EXISTS term_gene (
    term_id INTEGER NOT NULL,
    gene_id INTEGER NOT NULL,
    predicate_id INTEGER,
    source_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    value DOUBLE PRECISION,

    FOREIGN KEY (term_id) REFERENCES term(id) ON DELETE CASCADE,
    FOREIGN KEY (gene_id) REFERENCES gene(id) ON DELETE CASCADE,
    FOREIGN KEY (predicate_id) REFERENCES predicate(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES source(id),
    FOREIGN KEY (evidence_id) REFERENCES evidence(id)
);

CREATE TABLE IF NOT EXISTS term_channel (
    term_id INTEGER NOT NULL,
    sample_id INTEGER NOT NULL,
    channel SMALLINT NOT NULL,
    source_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    value DOUBLE PRECISION,
    probability DOUBLE PRECISION,

    FOREIGN KEY (term_id) REFERENCES term(id) ON DELETE CASCADE,
    FOREIGN KEY (sample_id, channel) 
        REFERENCES channel(sample_id, channel) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES source(id),
    FOREIGN KEY (evidence_id) REFERENCES evidence(id)
);
