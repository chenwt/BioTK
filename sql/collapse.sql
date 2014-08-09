SELECT g.id as gene_id, 
    pv.sample_id, pv.channel, 
    CASE WHEN q.mean<100 THEN 
        avg(pv.value) 
    ELSE avg(log(pv.value-q.minimum+1)) 
    END AS value 
FROM gene g 
INNER JOIN probe_gene 
    ON probe_gene.gene_id=g.id 
INNER JOIN probe_value pv 
    ON pv.probe_id=probe_gene.probe_id 
INNER JOIN (
        SELECT sample_id, channel, 
            AVG(value) AS mean, 
            MIN(value) as minimum
        FROM probe_value 
        WHERE sample_id BETWEEN 17354312 AND 17354322 
        GROUP BY sample_id, channel
    ) by_channel
    ON by_channel.sample_id=pv.sample_id AND by_channel.channel=pv.channel 
INNER JOIN (
        SELECT probe_value.probe_id, probe_value.gene_id, AVG(probe_value.value)
        FROM probe_value
        INNER JOIN probe_gene
        ON probe_gene.probe_id=probe_value.probe_id
        GROUP BY probe_id
        ) by_probe
    ON probe_gene.probe_id=by_probe.probe_id
GROUP BY g.id, pv.sample_id, pv.channel, q.mean
LIMIT 20;
