--INSERT INTO gene_data
SELECT sample_id, channel, gene.id AS gene_id, gene_data[gene_index(gene.id)] AS value
FROM channel
INNER JOIN taxon
ON taxon.id=channel.taxon_id
INNER JOIN gene
ON gene.taxon_id=taxon.id
WHERE gene_data IS NOT NULL
    AND gene.id=7157
    AND gene_data[gene_index(gene.id)] NOT IN (NULL, 'NaN'::double precision)
LIMIT 50;
