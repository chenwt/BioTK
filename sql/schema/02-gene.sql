-- Genes and taxa

CREATE TABLE IF NOT EXISTS taxon (
    PRIMARY KEY (id),
    UNIQUE (accession),
    UNIQUE (name)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS gene (
    taxon_id BIGINT,
    symbol VARCHAR,
    data JSON,
    
    PRIMARY KEY (id),
    UNIQUE (accession),

    FOREIGN KEY (taxon_id) REFERENCES taxon (id) ON DELETE CASCADE
) INHERITS (entity);
