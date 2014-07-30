DROP VIEW IF EXISTS channel_data_by_taxon;
DROP VIEW IF EXISTS channel_data_by_accession;
DROP VIEW IF EXISTS channel_text;
DROP FUNCTION IF EXISTS age_distribution(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS age_distribution_summary(INTEGER);
DROP VIEW IF EXISTS age_distribution_summary;
DROP FUNCTION IF EXISTS gene_index(INTEGER);
DROP FUNCTION IF EXISTS gene_tissue_zscore(INTEGER, VARCHAR);

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

CREATE VIEW channel_data_by_accession
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

CREATE VIEW channel_text AS
    SELECT sample.id AS sample_id, 
        channel.channel,channel.taxon_id,
        sample.title || sample.description 
            AS sample_text,
        channel.source_name || channel.characteristics 
            AS channel_text
    FROM channel
    INNER JOIN sample
    ON channel.sample_id=sample.id;

CREATE OR REPLACE FUNCTION query_gene(q VARCHAR) 
RETURNS TABLE("Entrez ID" INTEGER, "Symbol" VARCHAR, "Name" VARCHAR, "Species" VARCHAR)
AS $$
BEGIN
    RETURN QUERY 
        SELECT gene.id, gene.symbol, gene.name, taxon.name
        FROM gene
        INNER JOIN taxon
        ON gene.taxon_id=taxon.id
        WHERE gene.name ILIKE '%' || q || '%'
        OR gene.symbol ILIKE '%' || q || '%';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION age_term_id()
RETURNS INTEGER AS $$
    SELECT term.id
        FROM term
        INNER JOIN ontology
        ON term.ontology_id=ontology.id
        WHERE ontology.prefix='PATO' 
            AND term.name='age'
        LIMIT 1
$$ LANGUAGE SQL IMMUTABLE;

CREATE FUNCTION age_distribution(taxon_id INTEGER) 
RETURNS TABLE("Age" DOUBLE PRECISION)
--RETURNS SETOF DOUBLE PRECISION
AS $$
    SELECT term_channel.value 
    FROM term 
    INNER JOIN term_channel 
        ON term_channel.term_id=term.id 
    INNER JOIN channel 
        ON channel.sample_id=term_channel.sample_id 
            AND term_channel.channel=channel.channel 
    WHERE channel.taxon_id=$1
        AND term.id=age_term_id()
        AND term_channel.value IS NOT NULL;
$$ LANGUAGE SQL;

CREATE VIEW age_distribution_summary AS
    SELECT * FROM (
        SELECT taxon.id AS "Taxon ID", taxon.name as "Species", 
            COUNT(q.*) AS "N", 
            ROUND(CAST(AVG(q."Age") AS numeric), 3) AS "Mean", 
            ROUND(CAST(STDDEV(q."Age") AS numeric), 3) AS "Standard Deviation"
        FROM taxon,
        LATERAL (SELECT * FROM age_distribution(taxon.id)) q
        GROUP BY taxon.id) AS summary
    WHERE summary."N" > 0
    ORDER BY summary."N" DESC;

CREATE OR REPLACE FUNCTION gene_taxon_id(gene_id INTEGER)
RETURNS INTEGER AS $$
    SELECT taxon_id
    FROM gene
    WHERE gene.id=gene_id
    LIMIT 1;
$$ LANGUAGE SQL IMMUTABLE;

CREATE FUNCTION gene_index(gene_id INTEGER)
RETURNS INTEGER AS $$
DECLARE taxid INTEGER;
DECLARE idx INTEGER;
BEGIN
    SELECT t.id INTO taxid
        FROM taxon t
        INNER JOIN gene g
        ON g.taxon_id=t.id
        WHERE g.id = $1;

    SELECT i INTO idx FROM (
        SELECT row_number() OVER (ORDER BY id) AS i, id
        FROM gene
        WHERE gene.taxon_id=taxid
    ) AS q 
    WHERE q.id = $1
    LIMIT 1;

    RETURN idx;
END
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION gene_tissue_zscore
(gene_id INTEGER, tissue_text VARCHAR) 
RETURNS TABLE("Accession" VARCHAR, "Age" DOUBLE PRECISION, 
    "Z-Score" DOUBLE PRECISION)
AS $$
    SELECT s.accession AS "Accession", 
        ca."Age" AS "Age", 
        ch.gene_data[gene_index($1)] AS "Z-Score"
    FROM channel ch
    INNER JOIN sample s
    ON s.id=ch.sample_id
    INNER JOIN term_channel tc
    ON tc.sample_id=ch.sample_id
        AND tc.channel=ch.channel
    INNER JOIN term t
    ON t.id=tc.term_id
    INNER JOIN channel_age ca
    ON ch.sample_id=ca.sample_id
        AND ch.channel=ca.channel
    WHERE t.name LIKE $2
        AND ch.gene_data[gene_index($1)] != 'NaN'::float
        AND gene_taxon_id($1)=ch.taxon_id;
$$ LANGUAGE SQL;
