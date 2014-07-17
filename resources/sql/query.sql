DROP VIEW channel_data_by_taxon;
CREATE VIEW channel_data_by_taxon
    AS
    SELECT taxon.id as "Taxon", taxon.name as "Species", 
        SUM(CASE WHEN channel.probe_data IS NOT NULL THEN 1 ELSE 0 END) as "Probe Samples",
        SUM(CASE WHEN channel.gene_data IS NOT NULL THEN 1 ELSE 0 END) as "Gene Samples"
    FROM channel
    INNER JOIN taxon
    ON taxon.id=taxon_id
    GROUP BY taxon.id, taxon.name
    ORDER BY "Gene Samples" DESC;

DROP VIEW channel_data_by_accession;
CREATE OR REPLACE VIEW channel_data_by_accession
    AS
    SELECT 
        platform.accession as "Platform Accession", 
        platform.title as "Platform",
        taxon.name as "Species", 
        SUM(CASE WHEN channel.probe_data IS NOT NULL THEN 1 ELSE 0 END) as "Probe Samples",
        SUM(CASE WHEN channel.gene_data IS NOT NULL THEN 1 ELSE 0 END) as "Gene Samples"
    FROM channel
    INNER JOIN sample
    ON channel.sample_id=sample.id
    INNER JOIN platform
    ON platform.id=sample.platform_id
    INNER JOIN taxon
    ON taxon.id=channel.taxon_id
    GROUP BY platform.accession, platform.title, taxon.id, taxon.name
    ORDER BY "Gene Samples" DESC;
