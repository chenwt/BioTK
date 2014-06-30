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
    
    FOREIGN KEY (taxon_id) REFERENCES taxon (id)
);

-- Datasets

CREATE TABLE IF NOT EXISTS platform (
    id SERIAL PRIMARY KEY,
    accession VARCHAR,
    title VARCHAR,
    manufacturer VARCHAR
);

CREATE TABLE IF NOT EXISTS series (
    id SERIAL PRIMARY KEY,
    accession VARCHAR,
    "type" VARCHAR,
    summary VARCHAR,
    design VARCHAR,
    submission_date DATE,
    title VARCHAR
);

CREATE TABLE IF NOT EXISTS sample (
    id SERIAL PRIMARY KEY,
    accession VARCHAR,
    platform_id INTEGER,
    taxon_id INTEGER,

    title VARCHAR,
    "type" VARCHAR,
    source VARCHAR,
    molecule VARCHAR,
    channel_count INTEGER,
    description VARCHAR,
    characteristics VARCHAR,

    data double precision[],

    FOREIGN KEY(taxon_id) REFERENCES taxon(id),
    FOREIGN KEY(platform_id) REFERENCES platform(id)
);

CREATE OR REPLACE VIEW sample_text AS 
SELECT * FROM (
    SELECT id, (title || ' ' || source || ' ' 
        || description || ' ' || characteristics) AS text
    FROM sample) AS q
WHERE text IS NOT NULL;

CREATE TABLE IF NOT EXISTS sample_series (
    sample_id INTEGER,
    series_id INTEGER,

    FOREIGN KEY (sample_id) REFERENCES sample(id),
    FOREIGN KEY (series_id) REFERENCES series(id)
);

-- Publications

CREATE TABLE IF NOT EXISTS journal (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    issn VARCHAR
);

CREATE TABLE IF NOT EXISTS publication (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER,
    pubmed_id INTEGER,
    title VARCHAR,
    abstract VARCHAR,

    FOREIGN KEY (journal_id) REFERENCES journal (id)
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

    FOREIGN KEY (ontology_id) REFERENCES ontology(id),
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

    FOREIGN KEY (agent_id) REFERENCES term(id),
    FOREIGN KEY (target_id) REFERENCES term(id),
    FOREIGN KEY (relationship_id) REFERENCES relationship(id)
);

-- Gene and sample annotation

CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS source (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS term_gene (
    term_id INTEGER NOT NULL,
    gene_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    value DOUBLE PRECISION,

    FOREIGN KEY (term_id) REFERENCES term(id),
    FOREIGN KEY (gene_id) REFERENCES gene(id)
);

CREATE TABLE IF NOT EXISTS term_sample (
    term_id INTEGER NOT NULL,
    sample_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    value DOUBLE PRECISION,

    FOREIGN KEY (term_id) REFERENCES term(id),
    FOREIGN KEY (sample_id) REFERENCES sample(id)
);

-- Synonyms

CREATE TABLE IF NOT EXISTS "synonym" (
    id SERIAL PRIMARY KEY,
    text VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS term_synonym (
    term_id INTEGER,
    synonym_id INTEGER,

    FOREIGN KEY (term_id) REFERENCES term(id),
    FOREIGN KEY (synonym_id) REFERENCES "synonym"(id)
);

CREATE TABLE IF NOT EXISTS gene_synonym (
    gene_id INTEGER,
    synonym_id INTEGER,

    FOREIGN KEY (gene_id) REFERENCES gene(id),
    FOREIGN KEY (synonym_id) REFERENCES "synonym"(id)
);


