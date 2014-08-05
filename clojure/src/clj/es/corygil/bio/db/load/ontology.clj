(ns es.corygil.bio.db.load.ontology
  (:require
    [es.corygil.bio.db.query :as ?] 
    [clojure.tools.logging :as log]
    [loom.attr :refer [attrs attr]]
    [loom.graph :refer [nodes edges]]
    [es.corygil.bio.db.core :as db 
     :reload true
     :refer [query insert! execute! insert-relations!]]
    [es.corygil.bio.ontology :refer [make-ontology-graph] :reload true]
    [es.corygil.io :refer [download]])
  (:import
    [org.biojava3.ontology Triple Ontology]
    [es.corygil.bio.ontology Term]))

(defn read-ontology [prefix ontology-name]
  (let [parser (org.biojava3.ontology.io.OboParser.)
        url (java.net.URL.
              (format "http://berkeleybop.org/ontologies/%s.obo" 
                      (.toLowerCase (name prefix))))]
    (with-open [rdr (clojure.java.io/reader (download url))]
      (.parseOBO parser rdr (name prefix) 
                 ontology-name))))
 
(defn term? [t]
  (and 
    (not (.contains t " "))
    (.contains t ":")))

(defn ontology-triples [o]
  (filter (fn [[s o p]]
            (and (term? s) (term? o)))
          (for [triple (.getTerms o)
                :when (instance? Triple triple)]
            [(.getName (.getSubject triple)) 
             (.getName (.getObject triple))
             (keyword 
               (.getName (.getPredicate triple)))])))

(defn ontology-terms [o]
  (for [t (.getTerms o)
        :let [accession (.getName t)]
        :when (and 
                (not (instance? Triple t))
                (.getDescription t)
                (term? (.getName t)))]
    (Term. nil 
           (.getName t)
           (.getDescription t)
           (vec (map #(.getName %) (.getSynonyms t))))))

(defn ontology-graph [#^Ontology o]
  (make-ontology-graph (keyword (.getName o)) (.getDescription o)
                       (ontology-terms o)
                       (ontology-triples o)
                       :node-key :accession))


(defn synonym-map []
  (?/kv-map :synonym))

(defn term-map [ontology-id]
  (?/->map
    (format "SELECT accession,id 
            FROM term
            WHERE ontology_id=%s" ontology-id)))

(defn load-ontology-graph! [g]
  ; Insert ontology
  (log/info (format "[%s] - Inserting ontology" (name (:prefix g))))
  (let [ontology-id 
        (->
          (query 
            ["INSERT INTO ontology (accession,name) 
             VALUES (?,?) 
             RETURNING id;" 
             (name (:prefix g)) (:name g)])
          first :id)]

    ; Insert terms
    (log/info (format "[%s] - Inserting term" (name (:prefix g))))
    (insert! "term" ["ontology_id" "accession" "name"]
             (for [t (map (partial attrs g) (nodes g))]
               [ontology-id (:accession t) (:name t)]))

    ; Insert synonyms
    (log/info (format "[%s] - Inserting synonym" (name (:prefix g))))
    (let [current-synonyms (synonym-map)]
      (insert! "synonym" ["value"]
             (set
               (for [n (nodes g)
                     s (:synonyms (attrs g n))
                     :when (not (current-synonyms s))]
                 [s]))))

    ; Insert term-synonym links
    (log/info (format "[%s] - Inserting entity_synonym" (name (:prefix g))))
    (let [term-id-map (term-map ontology-id)
          synonym-id-map (synonym-map)]
      (insert! "entity_synonym" ["entity_id" "synonym_id"]
               (set
                 (for [n (nodes g)
                       s (:synonyms (attrs g n))]
                   [(term-id-map n) (synonym-id-map s)]))))

     ; Insert predicates
    (log/info (format "[%s] - Inserting predicate" (name (:prefix g))))
    (doseq [p (set
                (map (fn [e] 
                       (:predicate (attrs g e)))
                     (edges g)))]
      (?/->key-id! :predicate p))
 
    ; Insert term-term links
    (log/info (format "[%s] - Inserting relation" (name (:prefix g))))
    (let [predicate-id-map (?/kv-map :predicate)
          term-id-map (term-map ontology-id)
          source-id (?/->key-id! :source (name (:prefix g)))
          evidence-id (?/->key-id! :evidence "manual")]
      (insert-relations!
        (set
          (for [e (edges g)
                :let [s (term-id-map (:src e))
                      d (term-id-map (:dest e))
                      p (predicate-id-map 
                          (name
                            (:predicate (attrs g e))))]
                :when (and s d p)]
            [s d p source-id evidence-id nil nil]))))
    (log/info "Insert complete for" (:name g))))

(def ontologies
  {:BTO "Brenda Tissue Ontology"
   :GO "Gene Ontology"
   :PATO "Phenotypic Quality Ontology"})

(defn load-ontology! [prefix ontology-name]
  (let [o (read-ontology prefix ontology-name)]
    (load-ontology-graph!
      (make-ontology-graph prefix ontology-name
                           (ontology-terms o)
                           (ontology-triples o)))))

(defn load-ontologies! []
  (doall
    (pmap (fn [[p n]] (load-ontology! p n))
          ontologies)))
