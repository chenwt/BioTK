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
    WHERE t.name=tissue
$$ LANGUAGE SQL; 
