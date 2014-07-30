SELECT * FROM (
    SELECT ch.gene_data[gene_index(?)] AS "Z-Score", tc1.value AS "Age"
    FROM channel ch
    INNER JOIN term_channel tc1
    ON tc1.sample_id=ch.sample_id
    AND tc1.channel=ch.channel
    AND tc1.term_id=age_term_id()
    LIMIT 1000
) q
WHERE "Age" IS NOT NULL
AND "Z-Score" != 'NaN'::float
LIMIT 100;
