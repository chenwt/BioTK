CREATE EXTENSION hstore;

-- Base

CREATE TABLE IF NOT EXISTS taxon (
    id SERIAL PRIMARY KEY,
    name VARCHAR
);

CREATE TABLE IF NOT EXISTS gene (
    taxon_id INTEGER,
    id SERIAL PRIMARY KEY, 
    symbol VARCHAR,
    name VARCHAR,
    
    FOREIGN KEY (taxon_id) REFERENCES taxon (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS source (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE
);

-- Datasets

CREATE TABLE IF NOT EXISTS platform (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL,

    accession VARCHAR UNIQUE,
    title VARCHAR,
    manufacturer VARCHAR,

    FOREIGN KEY (source_id) REFERENCES source(id)
);

CREATE TABLE IF NOT EXISTS series (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL,

    accession VARCHAR UNIQUE,

    "type" VARCHAR,
    summary VARCHAR,
    design VARCHAR,
    submission_date DATE,
    title VARCHAR,

    FOREIGN KEY (source_id) REFERENCES source(id)
);

CREATE TABLE IF NOT EXISTS sample (
    id SERIAL PRIMARY KEY,

    platform_id INTEGER NOT NULL,

    accession VARCHAR UNIQUE NOT NULL,

    title VARCHAR,
    status VARCHAR,
    submission_date VARCHAR,
    last_update_date VARCHAR,
    "type" VARCHAR,
    hybridization_protocol VARCHAR,
    description VARCHAR,
    data_processing VARCHAR,
    contact VARCHAR,
    supplementary_file VARCHAR,
    channel_count INTEGER,

    FOREIGN KEY(platform_id) REFERENCES platform(id) ON DELETE CASCADE
);

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

    UNIQUE (platform_id, accession),

    FOREIGN KEY (platform_id) REFERENCES platform(id) ON DELETE CASCADE
);

CREATE TABLE probe_gene (
    probe_id INTEGER,
    gene_id INTEGER,

    PRIMARY KEY (probe_id, gene_id),
    FOREIGN KEY (probe_id) REFERENCES probe(id) ON DELETE CASCADE,
    FOREIGN KEY (gene_id) REFERENCES gene(id) ON DELETE CASCADE
);

-- Publications

CREATE TABLE IF NOT EXISTS journal (
    id SERIAL PRIMARY KEY,
    nlm_id INTEGER,
    name VARCHAR,
    issn VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS publication (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER,
    pubmed_id INTEGER UNIQUE,
    pmc_id INTEGER UNIQUE,

    title VARCHAR,
    abstract VARCHAR,
    full_text VARCHAR,

    parse JSON,

    FOREIGN KEY (journal_id) REFERENCES journal (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS publication_doi (
    publication_id INTEGER,
    doi VARCHAR UNIQUE,

    FOREIGN KEY (publication_id) REFERENCES publication(id) ON DELETE CASCADE
);

-- Ontologies

CREATE TABLE IF NOT EXISTS ontology (
    id SERIAL PRIMARY KEY,
    prefix VARCHAR UNIQUE,
    name VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS namespace (
    id SERIAL PRIMARY KEY,
    text VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS term (
    id SERIAL PRIMARY KEY,
    ontology_id INTEGER,
    namespace_id INTEGER,

    accession VARCHAR UNIQUE,
    name VARCHAR,

    FOREIGN KEY (ontology_id) REFERENCES ontology(id) ON DELETE CASCADE,
    FOREIGN KEY (namespace_id) REFERENCES namespace(id)
);

CREATE TABLE IF NOT EXISTS relationship (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS term_term (
    agent_id INTEGER,
    target_id INTEGER,
    relationship_id INTEGER,
    value DOUBLE PRECISION,

    PRIMARY KEY (agent_id, target_id, relationship_id),

    FOREIGN KEY (agent_id) REFERENCES term(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES term(id) ON DELETE CASCADE,
    FOREIGN KEY (relationship_id) REFERENCES relationship(id) ON DELETE CASCADE
);

-- Gene and sample annotation

CREATE TABLE IF NOT EXISTS term_gene (
    term_id INTEGER NOT NULL,
    gene_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    value DOUBLE PRECISION,

    FOREIGN KEY (term_id) REFERENCES term(id) ON DELETE CASCADE,
    FOREIGN KEY (gene_id) REFERENCES gene(id) ON DELETE CASCADE,
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

    FOREIGN KEY (term_id) REFERENCES term(id) ON DELETE CASCADE,
    FOREIGN KEY (sample_id, channel) REFERENCES channel(sample_id, channel) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES source(id),
    FOREIGN KEY (evidence_id) REFERENCES evidence(id)
);

-- Synonyms

CREATE TABLE IF NOT EXISTS "synonym" (
    id SERIAL PRIMARY KEY,
    text VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS term_synonym (
    term_id INTEGER,
    synonym_id INTEGER,

    PRIMARY KEY (term_id, synonym_id),

    FOREIGN KEY (term_id) REFERENCES term(id) ON DELETE CASCADE,
    FOREIGN KEY (synonym_id) REFERENCES "synonym"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS gene_synonym (
    gene_id INTEGER,
    synonym_id INTEGER,

    PRIMARY KEY (gene_id, synonym_id),

    FOREIGN KEY (gene_id) REFERENCES gene(id),
    FOREIGN KEY (synonym_id) REFERENCES "synonym"(id)
);
