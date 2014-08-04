(ns es.corygil.bio.ontology
  (:require
    [loom.attr :refer [add-attr add-attr-to-nodes add-attr-to-edges]]
    [loom.graph :refer [digraph add-edges add-nodes]]))

(defrecord Term [id accession name synonyms])

(defn make-ontology-graph [prefix ontology-name terms triples 
                            & {:keys [node-key]
                               :or {node-key :id}}]
  ; triples must have subject and object as node-key
  (assoc 
    (reduce
      (fn [g t]
        (reduce
          (fn [g [k v]]
            (add-attr g (node-key t) k v))
          (add-nodes g (node-key t))
          t))
      (reduce
       (fn [g [s o p]]
         (add-attr (add-edges g [s o])
                   [s o] :predicate p))
        (digraph)
        triples)
      terms)
    :prefix prefix :name ontology-name))

(defn gene-ontology-concepts []
  (?/rows))

(defn ontology-graph [prefix & {:keys [node-key]
                                :or {node-key :id}}]) 
