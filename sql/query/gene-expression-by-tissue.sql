SELECT "Accession", "Age", "Z-Score", "Tissue"
FROM (
    SELECT 
        ROW_NUMBER() OVER (PARTITION BY t.name) AS n,
        s.accession AS "Accession", 
        ca."Age" AS "Age", 
        ch.gene_data[gene_index(?)] AS "Z-Score",
        t.name AS "Tissue"
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
    WHERE t.name = ?
        AND o.prefix='BTO'
        AND ch.gene_data[gene_index(?)] != 'NaN'::float
        AND gene_taxon_id(?)=ch.taxon_id
) q 
WHERE q.n <= 100;
