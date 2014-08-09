ALTER TABLE probe_value ADD FOREIGN KEY
    fk_probe_value_sample_id
    (sample_id)
    REFERENCES sample(id);

ALTER TABLE probe_value ADD FOREIGN KEy
    fk_probe_value_sample_id_channel_id
    (sample_id, channel)
    REFERENCES channel(sample_id, channel);

CREATE INDEX probe_value_sample_id_idx
    ON probe_value(sample_id, channel);

CREATE INDEX probe_value_probe_id_idx
    ON probe_value(probe_id);
