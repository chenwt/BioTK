UPDATE gene
SET data=q.data
FROM (
    SELECT 
        g.id AS id, 
        hstore(array_agg(ch.sample_id || '-' || ch.channel),
            array_agg(round(
                ch.gene_data[gene_index(g.id)]::numeric,3)::text))
                AS data
        FROM
        gene g
        INNER JOIN channel ch
        ON ch.taxon_id=g.taxon_id
        WHERE ch.gene_data[gene_index(g.id)] IS NOT NULL
        GROUP BY g.id) q
WHERE gene.id=q.id;
