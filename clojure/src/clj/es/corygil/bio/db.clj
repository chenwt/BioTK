(ns es.corygil.bio.db
  (:use 
    es.corygil.bio.text)
  (:import
    [es.corygil.bio.text Synonym])
  (:require
    [clojure.java.jdbc :as sql]))

(defrecord Table [uuid name query rows columns])

(def spec
  (:database
    (load-file "config.clj")))

(defn view [view-name & {:keys [limit]}]
  (sql/query spec [(format "SELECT * FROM %s %s" 
                           (.replaceAll (name view-name) "-", "_")
                           (if limit (str "LIMIT " limit)))]
             :identifiers #(.replaceAll (.toLowerCase %) "_", "-")))

(defn ontology-synonyms [prefix]
  (for [[term-id text] 
        (rest
          (sql/query spec
                     ["SELECT t.id, s.text
                      FROM ontology o
                      INNER JOIN term t
                      ON t.ontology_id=o.id
                      INNER JOIN term_synonym ts
                      ON ts.term_id=t.id
                      INNER JOIN synonym s
                      ON ts.synonym_id=s.id
                      WHERE o.prefix=?
                      UNION
                      SELECT t.id, t.name
                      FROM ontology o
                      INNER JOIN term t
                      ON t.ontology_id=o.id
                      WHERE o.prefix=?;" prefix prefix]
                     :as-arrays? true))]
    (Synonym. term-id text)))

(defn extract-channel-tissues []
  (let [bto-chunker (chunker (ontology-synonyms "BTO"))]
    (for [c (take 200 (view :channel-text))
          :let [m (or (first (chunk bto-chunker (:channel-text c)))
                      (first (chunk bto-chunker (:sample-text c))))]
          :when m]
      (assoc (select-keys c [:sample-id :channel])
             :term-id (:id m)))))

(prn (take 5 (view :channel-text :limit 5)))

;(prn (extract-channel-tissues))
;(prn chunker)
