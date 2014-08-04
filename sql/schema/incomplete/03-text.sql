-- Publications
-- fixme.

RAISE 'document schema needs fixing';

CREATE TABLE document (
    fields (hstore),

    PRIMARY KEY(id)
) INHERITS (entity);

CREATE TABLE IF NOT EXISTS journal (
    id SERIAL PRIMARY KEY,
    nlm_id INTEGER,
    name VARCHAR,
    issn VARCHAR UNIQUE
);

CREATE TABLE IF NOT EXISTS publication (
    id SERIAL PRIMARY KEY,
    journal_id INTEGER,
    pubmed_id INTEGER UNIQUE,
    pmc_id INTEGER UNIQUE,

    title VARCHAR,
    abstract VARCHAR,
    full_text VARCHAR,

    parse JSON,

    FOREIGN KEY (journal_id) REFERENCES journal (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS publication_doi (
    publication_id INTEGER,
    doi VARCHAR UNIQUE,

    FOREIGN KEY (publication_id) REFERENCES publication(id) ON DELETE CASCADE
);
