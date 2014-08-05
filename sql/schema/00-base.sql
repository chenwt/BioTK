CREATE EXTENSION hstore;

-- Abstract tables

CREATE TABLE IF NOT EXISTS entity (
    id BIGSERIAL PRIMARY KEY,
    accession VARCHAR,
    name VARCHAR
);

CREATE RULE entity_is_abstract_table AS
    ON INSERT TO entity
    DO INSTEAD NOTHING
    ;

CREATE TABLE key_value (
    id SERIAL PRIMARY KEY,
    value VARCHAR
);

CREATE RULE key_value_is_abstract_table AS
    ON INSERT TO key_value
    DO INSTEAD NOTHING
    ;

-- Attribute tables

CREATE TABLE IF NOT EXISTS evidence (
    PRIMARY KEY (id),
    UNIQUE (value)
) INHERITS (key_value);

CREATE TABLE IF NOT EXISTS source (
    PRIMARY KEY (id),
    UNIQUE (value)
) INHERITS (key_value);

CREATE TABLE IF NOT EXISTS "synonym" (
    PRIMARY KEY (id),
    UNIQUE (value)
) INHERITS (key_value);

CREATE TABLE IF NOT EXISTS predicate (
    PRIMARY KEY (id),
    UNIQUE (value)
) INHERITS (key_value);

CREATE TABLE IF NOT EXISTS namespace (
    PRIMARY KEY (id),
    UNIQUE (value)
) INHERITS (key_value);

-- General join tables

--CREATE TABLE entity_accession (
--    entity_id INTEGER NOT NULL,
--    source_id INTEGER NOT NULL,
--    accession VARCHAR,
--    is_primary BOOLEAN,
--
--    UNIQUE (entity_id, source_id, accession),
--    FOREIGN KEY (entity_id) REFERENCES entity (id),
--    FOREIGN KEY (source_id) REFERENCES source (id)
--);
--
--CREATE FUNCTION primary_accession(entity_id INTEGER)
--RETURNS VARCHAR AS $$
--    SELECT accession FROM entity_accession
--        WHERE entity_id=$1 AND is_primary;
--$$ LANGUAGE SQL;
--

CREATE TABLE entity_synonym (
    entity_id INTEGER NOT NULL,
    synonym_id INTEGER NOT NULL,

    PRIMARY KEY (entity_id, synonym_id)
    --FOREIGN KEY (entity_id) REFERENCES entity (id),
    --FOREIGN KEY (synonym_id) REFERENCES synonym (id)
);

CREATE TABLE IF NOT EXISTS relation (
    id BIGSERIAL PRIMARY KEY,
    subject_id BIGINT NOT NULL,
    object_id BIGINT NOT NULL,
    predicate_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    evidence_id INTEGER NOT NULL,
    value DOUBLE PRECISION,
    probability DOUBLE PRECISION,

    UNIQUE (subject_id, object_id, predicate_id, source_id, evidence_id)
    --FOREIGN KEY (subject_id) REFERENCES entity(id) ON DELETE CASCADE,
    --FOREIGN KEY (object_id) REFERENCES entity(id) ON DELETE CASCADE,
    --FOREIGN KEY (predicate_id) REFERENCES predicate(id) ON DELETE CASCADE,
    --FOREIGN KEY (source_id) REFERENCES source(id) ON DELETE CASCADE,
    --FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

CREATE INDEX relation_subject_id_idx ON relation(subject_id);
CREATE INDEX relation_object_id_idx ON relation(object_id);
