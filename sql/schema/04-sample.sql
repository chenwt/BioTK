-- Datasets

CREATE TABLE IF NOT EXISTS platform (
    source_id INTEGER NOT NULL,

    manufacturer VARCHAR,

    PRIMARY KEY (id),
    UNIQUE (accession),
    FOREIGN KEY (source_id) REFERENCES source(id)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS series (
    source_id INTEGER NOT NULL,
    --pubmed_id INTEGER,

    title VARCHAR,
    summary VARCHAR,
    "type" VARCHAR,
    design VARCHAR,
    submission_date DATE,

    PRIMARY KEY (id),
    UNIQUE (accession),
    FOREIGN KEY (source_id) REFERENCES source(id)
    --FOREIGN KEY (pubmed_id) REFERENCES publication(pubmed_id)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS sample (
    platform_id BIGINT NOT NULL,

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

    PRIMARY KEY (id),
    UNIQUE (accession),
    FOREIGN KEY(platform_id) 
        REFERENCES platform(id) ON DELETE CASCADE
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS channel (
    sample_id BIGINT NOT NULL,
    channel SMALLINT NOT NULL,

    taxon_id BIGINT NOT NULL,

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
    sample_id BIGINT,
    series_id BIGINT,

    PRIMARY KEY (sample_id, series_id),
    FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
);

-- Probes & probe mappings

CREATE TABLE probe (
    platform_id INTEGER,

    PRIMARY KEY (id),
    UNIQUE (platform_id, accession),

    FOREIGN KEY (platform_id) REFERENCES platform(id) 
        ON DELETE CASCADE
) INHERITS (entity);

CREATE TABLE probe_value (
    probe_id BIGINT,
    sample_id BIGINT,
    channel SMALLINT,
    value DOUBLE PRECISION NOT NULL,

    PRIMARY KEY (probe_id,sample_id,channel),
    FOREIGN KEY (probe_id) REFERENCES probe(id)
        ON DELETE CASCADE,
    FOREIGN KEY (sample_id) REFERENCES sample(id)
        ON DELETE CASCADE,
    FOREIGN KEY (sample_id, channel) 
        REFERENCES channel(sample_id, channel)
        ON DELETE CASCADE
);

CREATE INDEX probe_value_probe_id_idx 
    ON probe_value(probe_id);
CREATE INDEX probe_value_sample_id_channel_idx
    ON probe_value(sample_id, channel);

CREATE TABLE probe_gene (
    probe_id BIGINT,
    gene_id BIGINT,

    PRIMARY KEY (probe_id, gene_id),
    FOREIGN KEY (probe_id) REFERENCES probe(id) 
        ON DELETE CASCADE,
    FOREIGN KEY (gene_id) REFERENCES gene(id) 
        ON DELETE CASCADE
);
