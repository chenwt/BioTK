SELECT s.accession,s.id
FROM sample s
INNER JOIN channel ch
ON ch.sample_id=s.id
WHERE ch.channel=1
AND ch.taxon_id=?;
