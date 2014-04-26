PRAGMA journal_mode=WAL;
PRAGMA synchronous=OFF;

-- for taxon, the id is NCBI taxon ID
-- for sample_id, platform_id, and series_id, the ID is
--   the number following GSM, GPL, and GSE, respectively

CREATE TABLE taxon (
    id INTEGER PRIMARY KEY NOT NULL
);

CREATE TABLE platform (
    id INTEGER PRIMARY KEY NOT NULL,
    title VARCHAR,
    manufacturer VARCHAR,
    taxon_id INT
);

CREATE TABLE feature_metadata (
    platform_id INTEGER NOT NULL,
    column_index INTEGER NOT NULL,
    name VARCHAR,
    description VARCHAR,

    PRIMARY KEY (platform_id, column_index)
);

CREATE TABLE feature (
    platform_id INTEGER NOT NULL,
    row_index INTEGER NOT NULL,
    column_index INTEGER NOT NULL,
    value VARCHAR,

    PRIMARY KEY (platform_id, row_index, column_index)
);

CREATE TABLE series (
    id INTEGER PRIMARY KEY NOT NULL,
    title VARCHAR,
    summary VARCHAR,
    overall_design VARCHAR
);

CREATE TABLE series_sample (
    series_id INTEGER NOT NULL,
    sample_id INTEGER NOT NULL,

    PRIMARY KEY (series_id, sample_id)
);

CREATE TABLE sample (
    id INTEGER PRIMARY KEY NOT NULL,
    platform_id INTEGER NOT NULL,
    title VARCHAR,
    description VARCHAR,
    channel_count INT
);

CREATE TABLE sample_data (
    sample_id INTEGER,
    channel INTEGER,
    data BLOB,
    PRIMARY KEY (sample_id, channel)
);

CREATE TABLE sample_characteristic (
    sample_id INTEGER NOT NULL,
    channel INTEGER NOT NULL,
    key VARCHAR NOT NULL,
    value VARCHAR
);

CREATE INDEX ix_sample_characteristic_sample_id ON sample_characteristic(sample_id);
