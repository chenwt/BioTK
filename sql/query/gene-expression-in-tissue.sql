EXPLAIN ANALYZE
SELECT 
    s.accession AS "Accession", 
    ca."Age" AS "Age", 
    ch.gene_data[gene_index(7157)] AS "Z-Score"
FROM channel ch
INNER JOIN sample s
    ON s.id=ch.sample_id
INNER JOIN term_channel tc
    ON tc.sample_id=ch.sample_id
        AND tc.channel=ch.channel
INNER JOIN term t
    ON t.id=tc.term_id
INNER JOIN ontology o
    ON t.ontology_id=o.id
INNER JOIN channel_age ca
    ON ch.sample_id=ca.sample_id
        AND ch.channel=ca.channel
WHERE t.name = 'heart'
    AND o.prefix='BTO'
    AND ch.gene_data[gene_index(7157)] != 'NaN'::float
    AND ch.taxon_id=9606
LIMIT 200;
