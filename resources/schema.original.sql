--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: hstore; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS hstore WITH SCHEMA public;


--
-- Name: EXTENSION hstore; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION hstore IS 'data type for storing sets of (key, value) pairs';


SET search_path = public, pg_catalog;

--
-- Name: channel_query_result; Type: TYPE; Schema: public; Owner: gilesc
--

CREATE TYPE channel_query_result AS (
	id bigint,
	accession character varying,
	taxon_id character varying
);


ALTER TYPE channel_query_result OWNER TO gilesc;

--
-- Name: annotated_samples(character varying); Type: FUNCTION; Schema: public; Owner: gilesc
--

CREATE FUNCTION annotated_samples(taxon character varying) RETURNS SETOF character varying
    LANGUAGE sql
    AS $$
    SELECT DISTINCT(ch.accession) as accession
    FROM channel ch
    INNER JOIN taxon t
    ON t.id=ch.taxon_id
    WHERE t.accession=taxon;
$$;


ALTER FUNCTION public.annotated_samples(taxon character varying) OWNER TO gilesc;

--
-- Name: annotated_samples(character varying, character varying); Type: FUNCTION; Schema: public; Owner: gilesc
--

CREATE FUNCTION annotated_samples(taxon character varying, tissue_accession character varying) RETURNS SETOF character varying
    LANGUAGE sql
    AS $$
    SELECT DISTINCT(ch.accession) as accession
    FROM channel ch
    INNER JOIN relation r
    ON r.subject_id=ch.id
    INNER JOIN predicate p
    ON p.id=r.predicate_id
    INNER JOIN term t
    ON t.id=r.object_id
    WHERE t.accession=tissue_accession
    INTERSECT
    SELECT * FROM annotated_samples(taxon);
$$;


ALTER FUNCTION public.annotated_samples(taxon character varying, tissue_accession character varying) OWNER TO gilesc;

--
-- Name: pato_tid(character varying); Type: FUNCTION; Schema: public; Owner: gilesc
--

CREATE FUNCTION pato_tid(q character varying) RETURNS bigint
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT id FROM term
    WHERE accession LIKE 'PATO:%'
    AND name=q
$$;


ALTER FUNCTION public.pato_tid(q character varying) OWNER TO gilesc;

--
-- Name: tid_age(); Type: FUNCTION; Schema: public; Owner: gilesc
--

CREATE FUNCTION tid_age() RETURNS bigint
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT id FROM term
    WHERE accession LIKE 'PATO:%'
    AND name='age'
$$;


ALTER FUNCTION public.tid_age() OWNER TO gilesc;

--
-- Name: tissue_channel(character varying); Type: FUNCTION; Schema: public; Owner: gilesc
--

CREATE FUNCTION tissue_channel(tissue character varying) RETURNS TABLE(channel_id bigint, taxon_id bigint, channel_accession character varying, taxon_accession character varying)
    LANGUAGE sql
    AS $$
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
$$;


ALTER FUNCTION public.tissue_channel(tissue character varying) OWNER TO gilesc;

--
-- Name: btree_hstore_ops; Type: OPERATOR FAMILY; Schema: public; Owner: postgres
--

CREATE OPERATOR FAMILY btree_hstore_ops USING btree;


ALTER OPERATOR FAMILY public.btree_hstore_ops USING btree OWNER TO postgres;

--
-- Name: gin_hstore_ops; Type: OPERATOR FAMILY; Schema: public; Owner: postgres
--

CREATE OPERATOR FAMILY gin_hstore_ops USING gin;


ALTER OPERATOR FAMILY public.gin_hstore_ops USING gin OWNER TO postgres;

--
-- Name: gist_hstore_ops; Type: OPERATOR FAMILY; Schema: public; Owner: postgres
--

CREATE OPERATOR FAMILY gist_hstore_ops USING gist;


ALTER OPERATOR FAMILY public.gist_hstore_ops USING gist OWNER TO postgres;

--
-- Name: hash_hstore_ops; Type: OPERATOR FAMILY; Schema: public; Owner: postgres
--

CREATE OPERATOR FAMILY hash_hstore_ops USING hash;


ALTER OPERATOR FAMILY public.hash_hstore_ops USING hash OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: entity; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE entity (
    id bigint NOT NULL,
    accession character varying,
    name character varying
);


ALTER TABLE entity OWNER TO gilesc;

--
-- Name: channel; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE channel (
    sample_id bigint NOT NULL,
    channel smallint NOT NULL,
    taxon_id bigint NOT NULL,
    source_name character varying,
    characteristics character varying,
    molecule character varying,
    label character varying,
    treatment_protocol character varying,
    extract_protocol character varying,
    label_protocol character varying
)
INHERITS (entity);


ALTER TABLE channel OWNER TO gilesc;

--
-- Name: relation; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE relation (
    id bigint NOT NULL,
    subject_id bigint NOT NULL,
    object_id bigint NOT NULL,
    predicate_id integer NOT NULL,
    source_id integer,
    evidence_id integer,
    value double precision,
    probability double precision
);


ALTER TABLE relation OWNER TO gilesc;

--
-- Name: channel_age; Type: VIEW; Schema: public; Owner: gilesc
--

CREATE VIEW channel_age AS
 SELECT ch.id AS channel_id,
    r.value AS age
   FROM (channel ch
     JOIN relation r ON ((ch.id = r.subject_id)))
  WHERE ((r.object_id = pato_tid('age'::character varying)) AND (r.value IS NOT NULL));


ALTER TABLE channel_age OWNER TO gilesc;

--
-- Name: channel_gender; Type: VIEW; Schema: public; Owner: gilesc
--

CREATE VIEW channel_gender AS
 SELECT ch.id AS channel_id,
    'M'::text AS gender
   FROM (channel ch
     JOIN relation r ON ((r.subject_id = ch.id)))
  WHERE (r.object_id = pato_tid('male'::character varying))
UNION
 SELECT ch.id AS channel_id,
    'F'::text AS gender
   FROM (channel ch
     JOIN relation r ON ((r.subject_id = ch.id)));


ALTER TABLE channel_gender OWNER TO gilesc;

--
-- Name: key_value; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE key_value (
    id integer NOT NULL,
    value character varying
);


ALTER TABLE key_value OWNER TO gilesc;

--
-- Name: predicate; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE predicate (
)
INHERITS (key_value);


ALTER TABLE predicate OWNER TO gilesc;

--
-- Name: term; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE term (
    ontology_id bigint,
    namespace_id integer
)
INHERITS (entity);


ALTER TABLE term OWNER TO gilesc;

--
-- Name: relation_closure; Type: MATERIALIZED VIEW; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE MATERIALIZED VIEW relation_closure AS
 WITH RECURSIVE closure(object_id, subject_id) AS (
         SELECT r.object_id,
            r.subject_id
           FROM (relation r
             JOIN predicate p ON ((p.id = r.predicate_id)))
          WHERE ((p.value)::text = ANY (ARRAY[('is_a'::character varying)::text, ('part_of'::character varying)::text]))
        UNION ALL
         SELECT tc.object_id,
            r.subject_id
           FROM closure tc,
            (relation r
             JOIN predicate p ON ((p.id = r.predicate_id)))
          WHERE (((p.value)::text = ANY (ARRAY[('is_a'::character varying)::text, ('part_of'::character varying)::text])) AND (r.object_id = tc.subject_id))
        )
 SELECT closure.object_id AS parent_id,
    closure.subject_id AS child_id
   FROM closure
UNION
 SELECT term.id AS parent_id,
    term.id AS child_id
   FROM term
  WITH NO DATA;


ALTER TABLE relation_closure OWNER TO gilesc;

--
-- Name: channel_tissue; Type: VIEW; Schema: public; Owner: gilesc
--

CREATE VIEW channel_tissue AS
 SELECT ch.id AS channel_id,
    t.accession AS tissue_accession,
    t.name AS tissue_name
   FROM ((((channel ch
     JOIN relation r ON ((r.subject_id = ch.id)))
     JOIN predicate p ON ((p.id = r.predicate_id)))
     JOIN relation_closure tc ON ((tc.child_id = r.object_id)))
     JOIN term t ON ((tc.parent_id = t.id)))
  WHERE ((t.accession)::text ~~ 'BTO:%'::text);


ALTER TABLE channel_tissue OWNER TO gilesc;

--
-- Name: sample_series; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE sample_series (
    sample_id bigint NOT NULL,
    series_id bigint NOT NULL
);


ALTER TABLE sample_series OWNER TO gilesc;

--
-- Name: series; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE series (
    title character varying,
    summary character varying,
    type character varying,
    design character varying,
    submission_date date
)
INHERITS (entity);


ALTER TABLE series OWNER TO gilesc;

--
-- Name: taxon; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE taxon (
)
INHERITS (entity);


ALTER TABLE taxon OWNER TO gilesc;

--
-- Name: channel_attribute; Type: MATERIALIZED VIEW; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE MATERIALIZED VIEW channel_attribute AS
 SELECT q.channel_id,
    ch.accession AS channel_accession,
    ssq.series_accession,
    t.accession AS taxon_accession,
    q.tissue_accession,
    q.tissue_name,
    q.age,
    q.gender
   FROM (((( SELECT ct.channel_id,
            ct.tissue_accession,
            ct.tissue_name,
            ca.age,
            cg.gender
           FROM ((channel_tissue ct
             FULL JOIN channel_age ca ON ((ca.channel_id = ct.channel_id)))
             FULL JOIN channel_gender cg ON ((ca.channel_id = cg.channel_id)))) q
     JOIN channel ch ON ((ch.id = q.channel_id)))
     JOIN taxon t ON ((ch.taxon_id = t.id)))
     LEFT JOIN ( SELECT ch_1.id AS channel_id,
            s.accession AS series_accession
           FROM ((sample_series ss
             JOIN channel ch_1 ON ((ss.sample_id = ch_1.sample_id)))
             JOIN series s ON ((s.id = ss.series_id)))) ssq ON ((ssq.channel_id = q.channel_id)))
  WITH NO DATA;


ALTER TABLE channel_attribute OWNER TO gilesc;

--
-- Name: entity_id_seq; Type: SEQUENCE; Schema: public; Owner: gilesc
--

CREATE SEQUENCE entity_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE entity_id_seq OWNER TO gilesc;

--
-- Name: entity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gilesc
--

ALTER SEQUENCE entity_id_seq OWNED BY entity.id;


--
-- Name: entity_synonym; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE entity_synonym (
    entity_id integer NOT NULL,
    synonym_id integer NOT NULL
);


ALTER TABLE entity_synonym OWNER TO gilesc;

--
-- Name: evidence; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE evidence (
)
INHERITS (key_value);


ALTER TABLE evidence OWNER TO gilesc;

--
-- Name: gene; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE gene (
    taxon_id bigint,
    symbol character varying
)
INHERITS (entity);


ALTER TABLE gene OWNER TO gilesc;

--
-- Name: key_value_id_seq; Type: SEQUENCE; Schema: public; Owner: gilesc
--

CREATE SEQUENCE key_value_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE key_value_id_seq OWNER TO gilesc;

--
-- Name: key_value_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gilesc
--

ALTER SEQUENCE key_value_id_seq OWNED BY key_value.id;


--
-- Name: namespace; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE namespace (
)
INHERITS (key_value);


ALTER TABLE namespace OWNER TO gilesc;

--
-- Name: ontology; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE ontology (
)
INHERITS (entity);


ALTER TABLE ontology OWNER TO gilesc;

--
-- Name: platform; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE platform (
    taxon_id integer,
    manufacturer character varying
)
INHERITS (entity);


ALTER TABLE platform OWNER TO gilesc;

--
-- Name: relation_id_seq; Type: SEQUENCE; Schema: public; Owner: gilesc
--

CREATE SEQUENCE relation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE relation_id_seq OWNER TO gilesc;

--
-- Name: relation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gilesc
--

ALTER SEQUENCE relation_id_seq OWNED BY relation.id;


--
-- Name: sample; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE sample (
    platform_id bigint NOT NULL,
    title character varying,
    description character varying,
    status character varying,
    submission_date character varying,
    last_update_date character varying,
    type character varying,
    hybridization_protocol character varying,
    data_processing character varying,
    contact character varying,
    supplementary_file character varying[],
    channel_count integer
)
INHERITS (entity);


ALTER TABLE sample OWNER TO gilesc;

--
-- Name: source; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE source (
)
INHERITS (key_value);


ALTER TABLE source OWNER TO gilesc;

--
-- Name: synonym; Type: TABLE; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE TABLE synonym (
)
INHERITS (key_value);


ALTER TABLE synonym OWNER TO gilesc;

--
-- Name: tissue_channel; Type: VIEW; Schema: public; Owner: gilesc
--

CREATE VIEW tissue_channel AS
 SELECT t.accession AS term_accession,
    t.name AS term_name,
    ch.accession AS channel_accession
   FROM (((((channel ch
     JOIN relation r ON ((r.subject_id = ch.id)))
     JOIN predicate p ON ((p.id = r.predicate_id)))
     JOIN relation_closure tc ON ((tc.child_id = r.object_id)))
     JOIN term t ON ((tc.parent_id = t.id)))
     JOIN taxon ON ((taxon.id = ch.taxon_id)))
  WHERE ((t.accession)::text ~~ 'BTO:%'::text);


ALTER TABLE tissue_channel OWNER TO gilesc;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY channel ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY entity ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY evidence ALTER COLUMN id SET DEFAULT nextval('key_value_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY gene ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY key_value ALTER COLUMN id SET DEFAULT nextval('key_value_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY namespace ALTER COLUMN id SET DEFAULT nextval('key_value_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY ontology ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY platform ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY predicate ALTER COLUMN id SET DEFAULT nextval('key_value_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY relation ALTER COLUMN id SET DEFAULT nextval('relation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY sample ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY series ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY source ALTER COLUMN id SET DEFAULT nextval('key_value_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY synonym ALTER COLUMN id SET DEFAULT nextval('key_value_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY taxon ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY term ALTER COLUMN id SET DEFAULT nextval('entity_id_seq'::regclass);


--
-- Name: channel_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY channel
    ADD CONSTRAINT channel_accession_key UNIQUE (accession);


--
-- Name: channel_sample_id_channel_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY channel
    ADD CONSTRAINT channel_sample_id_channel_key UNIQUE (sample_id, channel);


--
-- Name: entity_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY entity
    ADD CONSTRAINT entity_pkey PRIMARY KEY (id);


--
-- Name: entity_synonym_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY entity_synonym
    ADD CONSTRAINT entity_synonym_pkey PRIMARY KEY (entity_id, synonym_id);


--
-- Name: evidence_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY evidence
    ADD CONSTRAINT evidence_pkey PRIMARY KEY (id);


--
-- Name: evidence_value_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY evidence
    ADD CONSTRAINT evidence_value_key UNIQUE (value);


--
-- Name: gene_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY gene
    ADD CONSTRAINT gene_accession_key UNIQUE (accession);


--
-- Name: gene_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY gene
    ADD CONSTRAINT gene_pkey PRIMARY KEY (id);


--
-- Name: key_value_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY key_value
    ADD CONSTRAINT key_value_pkey PRIMARY KEY (id);


--
-- Name: namespace_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY namespace
    ADD CONSTRAINT namespace_pkey PRIMARY KEY (id);


--
-- Name: namespace_value_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY namespace
    ADD CONSTRAINT namespace_value_key UNIQUE (value);


--
-- Name: ontology_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY ontology
    ADD CONSTRAINT ontology_accession_key UNIQUE (accession);


--
-- Name: ontology_name_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY ontology
    ADD CONSTRAINT ontology_name_key UNIQUE (name);


--
-- Name: ontology_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY ontology
    ADD CONSTRAINT ontology_pkey PRIMARY KEY (id);


--
-- Name: platform_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY platform
    ADD CONSTRAINT platform_accession_key UNIQUE (accession);


--
-- Name: platform_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY platform
    ADD CONSTRAINT platform_pkey PRIMARY KEY (id);


--
-- Name: predicate_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY predicate
    ADD CONSTRAINT predicate_pkey PRIMARY KEY (id);


--
-- Name: predicate_value_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY predicate
    ADD CONSTRAINT predicate_value_key UNIQUE (value);


--
-- Name: relation_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY relation
    ADD CONSTRAINT relation_pkey PRIMARY KEY (id);


--
-- Name: relation_subject_id_object_id_predicate_id_source_id_eviden_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY relation
    ADD CONSTRAINT relation_subject_id_object_id_predicate_id_source_id_eviden_key UNIQUE (subject_id, object_id, predicate_id, source_id, evidence_id);


--
-- Name: sample_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY sample
    ADD CONSTRAINT sample_accession_key UNIQUE (accession);


--
-- Name: sample_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY sample
    ADD CONSTRAINT sample_pkey PRIMARY KEY (id);


--
-- Name: sample_series_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY sample_series
    ADD CONSTRAINT sample_series_pkey PRIMARY KEY (sample_id, series_id);


--
-- Name: series_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY series
    ADD CONSTRAINT series_accession_key UNIQUE (accession);


--
-- Name: series_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY series
    ADD CONSTRAINT series_pkey PRIMARY KEY (id);


--
-- Name: source_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY source
    ADD CONSTRAINT source_pkey PRIMARY KEY (id);


--
-- Name: source_value_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY source
    ADD CONSTRAINT source_value_key UNIQUE (value);


--
-- Name: synonym_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY synonym
    ADD CONSTRAINT synonym_pkey PRIMARY KEY (id);


--
-- Name: synonym_value_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY synonym
    ADD CONSTRAINT synonym_value_key UNIQUE (value);


--
-- Name: taxon_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY taxon
    ADD CONSTRAINT taxon_accession_key UNIQUE (accession);


--
-- Name: taxon_name_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY taxon
    ADD CONSTRAINT taxon_name_key UNIQUE (name);


--
-- Name: taxon_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY taxon
    ADD CONSTRAINT taxon_pkey PRIMARY KEY (id);


--
-- Name: term_accession_key; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY term
    ADD CONSTRAINT term_accession_key UNIQUE (accession);


--
-- Name: term_pkey; Type: CONSTRAINT; Schema: public; Owner: gilesc; Tablespace: 
--

ALTER TABLE ONLY term
    ADD CONSTRAINT term_pkey PRIMARY KEY (id);


--
-- Name: relation_object_id_idx; Type: INDEX; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE INDEX relation_object_id_idx ON relation USING btree (object_id);


--
-- Name: relation_subject_id_idx; Type: INDEX; Schema: public; Owner: gilesc; Tablespace: 
--

CREATE INDEX relation_subject_id_idx ON relation USING btree (subject_id);


--
-- Name: entity_is_abstract_table; Type: RULE; Schema: public; Owner: gilesc
--

CREATE RULE entity_is_abstract_table AS
    ON INSERT TO entity DO INSTEAD NOTHING;


--
-- Name: key_value_is_abstract_table; Type: RULE; Schema: public; Owner: gilesc
--

CREATE RULE key_value_is_abstract_table AS
    ON INSERT TO key_value DO INSTEAD NOTHING;


--
-- Name: channel_sample_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY channel
    ADD CONSTRAINT channel_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE;


--
-- Name: channel_taxon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY channel
    ADD CONSTRAINT channel_taxon_id_fkey FOREIGN KEY (taxon_id) REFERENCES taxon(id) ON DELETE CASCADE;


--
-- Name: gene_taxon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY gene
    ADD CONSTRAINT gene_taxon_id_fkey FOREIGN KEY (taxon_id) REFERENCES taxon(id) ON DELETE CASCADE;


--
-- Name: platform_taxon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY platform
    ADD CONSTRAINT platform_taxon_id_fkey FOREIGN KEY (taxon_id) REFERENCES taxon(id);


--
-- Name: sample_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY sample
    ADD CONSTRAINT sample_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES platform(id) ON DELETE CASCADE;


--
-- Name: sample_series_sample_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY sample_series
    ADD CONSTRAINT sample_series_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE;


--
-- Name: sample_series_series_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY sample_series
    ADD CONSTRAINT sample_series_series_id_fkey FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE;


--
-- Name: term_namespace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY term
    ADD CONSTRAINT term_namespace_id_fkey FOREIGN KEY (namespace_id) REFERENCES namespace(id);


--
-- Name: term_ontology_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gilesc
--

ALTER TABLE ONLY term
    ADD CONSTRAINT term_ontology_id_fkey FOREIGN KEY (ontology_id) REFERENCES ontology(id) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

