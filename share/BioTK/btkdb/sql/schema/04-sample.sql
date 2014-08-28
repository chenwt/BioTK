-- Datasets

CREATE TABLE IF NOT EXISTS platform (
    --source_id INTEGER NOT NULL,

    taxon_id INTEGER,
    manufacturer VARCHAR,

    PRIMARY KEY (id),
    UNIQUE (accession),
    FOREIGN KEY (taxon_id) REFERENCES taxon(id)
    --FOREIGN KEY (source_id) REFERENCES source(id)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS series (
    --source_id INTEGER NOT NULL,
    --pubmed_id INTEGER,

    title VARCHAR,
    summary VARCHAR,
    "type" VARCHAR,
    design VARCHAR,
    submission_date DATE,

    PRIMARY KEY (id),
    UNIQUE (accession)
    --FOREIGN KEY (source_id) REFERENCES source(id)
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

    PRIMARY KEY (sample_id, channel),
    FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE,
    FOREIGN KEY (taxon_id) REFERENCES taxon(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sample_series (
    sample_id BIGINT,
    series_id BIGINT,

    PRIMARY KEY (sample_id, series_id),
    FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
);

--CREATE OR REPLACE VIEW sample_text AS 
--SELECT * FROM (
--    SELECT id, (title || ' ' || source_name || ' ' 
--        || description || ' ' || characteristics) AS text
--    FROM sample) AS q
--WHERE text IS NOT NULL;


-- Probes & probe mappings

--CREATE TABLE IF NOT EXISTS probe (
--    platform_id INTEGER,
--
--    PRIMARY KEY (id),
--    UNIQUE (platform_id, accession),
--
--    FOREIGN KEY (platform_id) REFERENCES platform(id) 
--        ON DELETE CASCADE
--) INHERITS (entity);
--
--CREATE TABLE IF NOT EXISTS probe_value (
--    probe_id BIGINT,
--    sample_id BIGINT,
--    channel SMALLINT,
--    value DOUBLE PRECISION NOT NULL,
--
--    PRIMARY KEY (probe_id,sample_id,channel),
--    FOREIGN KEY (probe_id) REFERENCES probe(id)
--        ON DELETE CASCADE,
--    FOREIGN KEY (sample_id) REFERENCES sample(id)
--        ON DELETE CASCADE,
--    FOREIGN KEY (sample_id, channel) 
--        REFERENCES channel(sample_id, channel)
--        ON DELETE CASCADE
--);
--
--CREATE INDEX probe_value_probe_id_idx 
--    ON probe_value(probe_id);
--CREATE INDEX probe_value_sample_id_channel_idx
--    ON probe_value(sample_id, channel);
--
--CREATE TABLE probe_gene (
--    probe_id BIGINT,
--    gene_id BIGINT,
--
--    UNIQUE (probe_id, gene_id),
--    -- indexes and FKs added in add-index-probe-value.sql
--
--    --FOREIGN KEY (probe_id) REFERENCES probe(id),
--    --FOREIGN KEY (gene_id) REFERENCES gene(id)
--);
--
--CREATE MATERIALIZED VIEW probe_gene_collapsed (
--    probe_id, gene_id
--) AS ( 
--    WITH probe_summary AS (
--        SELECT 
--            ROW_NUMBER() OVER (
--                PARTITION BY probe_value.probe_id 
--                ORDER BY AVG(probe_value.value) DESC
--                ) AS i,
--            probe_value.probe_id AS probe_id, 
--            probe_gene.gene_id AS gene_id, 
--            AVG(probe_value.value) AS mean
--        FROM probe_value
--        INNER JOIN probe_gene
--        ON probe_gene.probe_id=probe_value.probe_id
--        GROUP BY probe_gene.gene_id, probe_value.probe_id
--        ORDER BY mean DESC)
--    SELECT s.probe_id, s.gene_id
--        FROM probe_summary s
--        WHERE s.i = 1
--) WITH NO DATA;
--
--ALTER TABLE probe_gene_collapsed ADD CONSTRAINT
--    probe_gene_collapsed_probe_id_fkey
--    FOREIGN KEY (probe_id) REFERENCES probe(id);

--ALTER TABLE probe_gene_collapsed ADD CONSTRAINT
--    probe_gene_collapsed_gene_id_fkey
--    FOREIGN KEY (gene_id) REFERENCES gene(id);
--
--CREATE INDEX probe_gene_collapsed_probe_id_idx
--    ON probe_gene_collapsed(probe_id);
--CREATE INDEX probe_gene_collapsed_gene_id_idx
--    ON probe_gene_collapsed(gene_id);
--
--CREATE MATERIALIZED VIEW gene_value (
--    sample_id, channel, gene_id, value
--) AS (
--    SELECT 
--        pv.sample_id, pv.channel, 
--        g.id as gene_id, 
--        CASE WHEN q.mean<100 THEN 
--            avg(pv.value) 
--        ELSE avg(log(pv.value-q.minimum+1)) 
--        END AS value 
--    FROM gene g 
--    INNER JOIN probe_gene 
--        ON probe_gene.gene_id=g.id 
--    INNER JOIN probe_value pv 
--        ON pv.probe_id=probe_gene.probe_id 
--    INNER JOIN (
--        SELECT sample_id, channel, 
--            AVG(value) AS mean, 
--            MIN(value) as minimum
--        FROM probe_value 
--        WHERE sample_id BETWEEN 17354312 AND 17354322 
--        GROUP BY sample_id, channel
--    ) by_channel
--        ON by_channel.sample_id=pv.sample_id 
--            AND by_channel.channel=pv.channel 
--    GROUP BY g.id, pv.sample_id, pv.channel, q.mean
--) WITH NO DATA;
--
--CREATE INDEX gene_value_gene_id_idx
--    ON gene_value(gene_id);
--CREATE INDEX gene_value_sample_id_channel_idx
--    ON gene_value(sample_id,channel);
