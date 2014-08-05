(ns es.corygil.bio.db.load
  (:require
    [es.corygil.bio.db.load.gene]
    [es.corygil.bio.db.load.ontology]))

(defn -main []
  (future
    (es.corygil.bio.db.load.gene/load-taxonomy!)
    (es.corygil.bio.db.load.gene/load-gene!))
  (future
    (es.corygil.bio.db.load.ontology/load-ontologies!))
  )
