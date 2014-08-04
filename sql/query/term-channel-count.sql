SELECT t.name AS "Term", COUNT(t.*) AS "Samples"
FROM term t
INNER JOIN ontology o
ON t.ontology_id=o.id
INNER JOIN term_channel tc
ON tc.term_id=t.id
WHERE o.prefix=?
GROUP BY t.name
ORDER BY COUNT(t.*) DESC;
