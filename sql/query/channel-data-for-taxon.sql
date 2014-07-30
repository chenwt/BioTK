SELECT cd.* FROM channel_data_by_accession cd
INNER JOIN taxon 
ON taxon.name=cd."Species"
WHERE taxon.id=?;
