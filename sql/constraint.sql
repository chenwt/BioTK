CREATE OR REPLACE FUNCTION create_constraint_if_not_exists (
    t_name text, c_name text, constraint_sql text
    ) 
    RETURNS void AS
    $$
    BEGIN
        -- Look for our constraint
    IF NOT EXISTS (
        SELECT constraint_name 
        FROM information_schema.constraint_column_usage 
        WHERE table_name = t_name  
        AND constraint_name = c_name) THEN
            EXECUTE constraint_sql;
    END IF;
END;
$$ LANGUAGE 'plpgsql';

SELECT create_constraint_if_not_exists('term_channel',
    'ck_term_channel_probability_range',
    'ALTER TABLE term_channel 
        ADD CONSTRAINT ck_term_channel_probability_range
        CHECK ( probability IS NULL 
            OR ( probability >= 0 AND probability <= 1))');
