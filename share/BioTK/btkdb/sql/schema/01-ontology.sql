-- Ontologies

CREATE TABLE IF NOT EXISTS ontology (
    PRIMARY KEY (id),
    UNIQUE (name),
    UNIQUE (accession)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS term (
    ontology_id BIGINT,
    namespace_id INTEGER,

    PRIMARY KEY (id),
    UNIQUE (accession),

    FOREIGN KEY (ontology_id) REFERENCES ontology(id) 
        ON DELETE CASCADE,
    FOREIGN KEY (namespace_id) REFERENCES namespace(id)
) INHERITS (entity);
