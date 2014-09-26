CREATE MATERIALIZED VIEW relation_closure 
    (parent_id, child_id) 
AS
    WITH RECURSIVE closure(object_id, subject_id) AS (
            SELECT r.object_id as object_id, r.subject_id as subject_id
            FROM relation r
            INNER JOIN predicate p
            ON p.id=r.predicate_id
            WHERE p.value IN ('is_a', 'part_of')
        UNION ALL
            SELECT tc.object_id, r.subject_id
            FROM closure tc, relation r
            INNER JOIN predicate p
            ON p.id=r.predicate_id
            WHERE p.value IN ('is_a', 'part_of')
            AND r.object_id=tc.subject_id
            
    )
    SELECT object_id as parent_id, subject_id as child_id 
    FROM closure
    UNION
    SELECT term.id, term.id FROM term;

CREATE FUNCTION pato_tid(q VARCHAR)
RETURNS BIGINT
AS $$
    SELECT id FROM term
    WHERE accession LIKE 'PATO:%'
    AND name=q
$$ LANGUAGE SQL IMMUTABLE;

CREATE VIEW tissue_channel AS
    SELECT t.accession as term_accession,
        t.name as term_name,
        ch.accession as channel_accession
    FROM channel ch
    INNER JOIN relation r
    ON r.subject_id=ch.id
    INNER JOIN predicate p
    ON p.id=r.predicate_id
    INNER JOIN relation_closure tc
    ON tc.child_id=r.object_id
    INNER JOIN term t
    ON tc.parent_id=t.id
    INNER JOIN taxon
    ON taxon.id=ch.taxon_id
    WHERE t.accession LIKE 'BTO:%';

CREATE FUNCTION
    tissue_channel(tissue VARCHAR)
RETURNS TABLE(
    channel_id BIGINT, 
    taxon_id BIGINT,
    channel_accession VARCHAR, 
    taxon_accession VARCHAR
) AS $$
    SELECT ch.id, taxon.id, ch.accession, taxon.accession
    FROM channel ch
    INNER JOIN relation r
    ON r.subject_id=ch.id
    INNER JOIN predicate p
    ON p.id=r.predicate_id
    INNER JOIN relation_closure tc
    ON tc.child_id=r.object_id
    INNER JOIN term t
    ON tc.parent_id=t.id
    INNER JOIN taxon
    ON taxon.id=ch.taxon_id
    WHERE t.name=tissue OR t.accession=tissue
$$ LANGUAGE SQL; 

CREATE VIEW channel_tissue AS
    SELECT ch.id as channel_id, 
        t.accession as tissue_accession,
        t.name as tissue_name
    FROM channel ch
    INNER JOIN relation r
    ON r.subject_id=ch.id
    INNER JOIN predicate p
    ON p.id=r.predicate_id
    INNER JOIN relation_closure tc
    ON tc.child_id=r.object_id
    INNER JOIN term t
    ON tc.parent_id=t.id
    WHERE t.accession LIKE 'BTO:%';

CREATE VIEW channel_age AS
    SELECT ch.id as channel_id, r.value as age
        FROM channel ch
        INNER JOIN relation r
        ON ch.id=r.subject_id
        WHERE r.object_id=pato_tid('age')
        AND r.value IS NOT NULL;

CREATE VIEW channel_gender AS
    SELECT ch.id as channel_id, 'M' as gender
    FROM channel ch
    INNER JOIN relation r
    ON r.subject_id=ch.id
    WHERE r.object_id=pato_tid('male')
    UNION
    SELECT ch.id as channel_id, 'F' as gender
    FROM channel ch
    INNER JOIN relation r
    ON r.subject_id=ch.id;

CREATE MATERIALIZED VIEW channel_attribute AS
    SELECT 
        q.channel_id as channel_id,
        ch.accession as channel_accession,
        ssq.series_accession as series_accession,
        t.accession as taxon_accession,
        q.tissue_accession as tissue_accession,
        q.tissue_name as tissue_name,
        q.age as age,
        q.gender as gender
    FROM
    (
        SELECT 
            ct.channel_id as channel_id,
            ct.tissue_accession as tissue_accession,
            ct.tissue_name as tissue_name,
            ca.age as age,
            cg.gender as gender
        FROM channel_tissue ct
        FULL OUTER JOIN channel_age ca
        ON (ca.channel_id=ct.channel_id)
        FULL OUTER JOIN channel_gender cg
        ON (ca.channel_id=cg.channel_id)
    ) q
    INNER JOIN channel ch
    ON ch.id=q.channel_id
    INNER JOIN taxon t
    ON ch.taxon_id=t.id
    LEFT JOIN (
        SELECT 
            ch.id as channel_id, 
            s.accession as series_accession
        FROM sample_series ss
        INNER JOIN channel ch
        ON ss.sample_id=ch.sample_id
        INNER JOIN series s
        ON s.id=ss.series_id
    ) ssq
    ON ssq.channel_id=q.channel_id;
