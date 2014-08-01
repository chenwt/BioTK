CREATE MATERIALIZED VIEW channel_age AS 
    SELECT ch.sample_id AS sample_id, ch.channel AS channel, 
        tc.value AS "Age"
    FROM channel ch
    INNER JOIN term_channel tc
    ON tc.sample_id=ch.sample_id
        AND tc.channel=ch.channel
    INNER JOIN term t
    ON tc.term_id=t.id
    INNER JOIN ontology o
    ON t.ontology_id=o.id
    WHERE o.prefix='PATO'
        AND t.name='age'
        AND tc.value IS NOT NULL;

CREATE OR REPLACE VIEW ontology_synonyms AS
    SELECT o.prefix AS prefix, t.id AS id, t.name AS "synonym"
        FROM ontology o
        INNER JOIN term t
        ON o.id=t.ontology_id
    UNION
    SELECT o.prefix, t.id AS id, s.text AS "synonym"
        FROM ontology o
        INNER JOIN term t
        ON o.id=t.ontology_id
        INNER JOIN term_synonym ts
        ON ts.term_id=t.id
        INNER JOIN "synonym" s
        ON s.id=ts.synonym_id;
