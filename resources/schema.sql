/* NCBI data */

CREATE TABLE taxon (
    /* = NCBI taxon ID */
    id SERIAL PRIMARY KEY NOT NULL,
    name VARCHAR,
    common_name VARCHAR
);

CREATE TABLE gene (
    /* = Entrez Gene ID */
    id SERIAL PRIMARY KEY NOT NULL, 
    taxon_id INTEGER,
    symbol VARCHAR,
    name VARCHAR,
    synonyms VARCHAR[],

    FOREIGN KEY (taxon_id) REFERENCES taxon(id)
);

/* Instead add ortholog_group to gene ? */
CREATE TABLE orthology (
    first INTEGER,
    second INTEGER,

    FOREIGN KEY (first) REFERENCES gene(id),
    FOREIGN KEY (second) REFERENCES gene(id)
);

/* GEO (and eventually SRA) samples */

CREATE TABLE platform (
    id SERIAL PRIMARY KEY NOT NULL,
    name VARCHAR,
    manufacturer VARCHAR
);

CREATE TABLE series (
    id SERIAL PRIMARY KEY NOT NULL,

    title VARCHAR,
    summary VARCHAR,
    type VARCHAR,
    design VARCHAR,
    submission_date DATE
)

CREATE TABLE sample (
    id SERIAL PRIMARY KEY NOT NULL,
    accession VARCHAR UNIQUE,
    platform_id INTEGER NOT NULL,

    title VARCHAR,
    description VARCHAR,
    status VARCHAR,
    submission_date VARCHAR,
    last_update_date VARCHAR,
    type VARCHAR,
    hybridization_protocol VARCHAR,
    data_processing VARCHAR,
    contact VARCHAR,
    supplementary_file VARCHAR[],
    channel_count INTEGER
)

CREATE TABLE channel (
    id SERIAL PRIMARY KEY NOT NULL,
    accession VARCHAR UNIQUE,

    sample_id INTEGER NOT NULL,
    channel SMALLINT NOT NULL,
    taxon_id INTEGER NOT NULL,

    source_name VARCHAR,
    characteristics VARCHAR,
    molecule VARCHAR,
    label VARCHAR,
    treatment_protocol VARCHAR,
    extract_protocol VARCHAR,
    label_protocol VARCHAR
);

/* Ontologies */
/* TODO: ontology links */

CREATE TABLE ontology (
    id SERIAL PRIMARY KEY NOT NULL,
    accession VARCHAR UNIQUE,
    name VARCHAR
);

CREATE TABLE term (
    ontology_id INTEGER NOT NULL,
    accession VARCHAR UNIQUE,
    namespace VARCHAR,

    synonyms VARCHAR[],

    FOREIGN KEY (ontology_id) REFERENCES ontology (id)
);

/* Annotations */

CREATE TABLE gene_annotation (
    gene_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    value DOUBLE PRECISION,
    /* probability DOUBLE PRECISION, */

    FOREIGN KEY (gene_id) REFERENCES gene(id),
    FOREIGN KEY (term_id) REFERENCES term(id)
);

CREATE TABLE channel_annotation (
    channel_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    value DOUBLE PRECISION,
    /* probability DOUBLE PRECISION, */

    FOREIGN KEY (channel_id) REFERENCES channel(id),
    FOREIGN KEY (term_id) REFERENCES term(id)
);

/* Text */

CREATE TABLE article (
    /* Pubmed ID */
    id SERIAL PRIMARY KEY NOT NULL,

    title VARCHAR,
    abstract VARCHAR
);
