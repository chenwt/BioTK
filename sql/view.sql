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
