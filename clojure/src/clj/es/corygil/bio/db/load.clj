(ns es.corygil.bio.db.load
  (:refer-clojure :exclude [source])
  (:use
    es.corygil.math)
  (:require
    [clojure.java.jdbc :as sql]
    [es.corygil.bio.db.core :as db]
    [es.corygil.text :as text]))

(def query (partial sql/query db/spec))
(def insert! (partial sql/insert! db/spec))

(defn insert-term-channel! [rows]
  (apply insert! "term_channel"
         ["term_id" "sample_id" "channel"
          "source_id" "evidence_id" "value" "probability"]
         rows))
 
(def patterns
  {:age #"\bage( *\((?<unitx>[a-z]*)\))?:[ \t]*(?<age>\d+[\.0-9]*)(( *\- *| (to|or) )(?<end>\d+[\.\d]*))?([ \t]*(?<unity> [a-z]+))?"
   :age-unit #"(age\s*unit[s]*|unit[s]* of age): (?<unit>[a-z])"
   :tissue #"(cell type|tissue|organ) *: *(?<tissue>[A-Za-z0-9\+\- ]+)"})

(def matchers
  (into {}
        (for [[k v] patterns]
          [k (.matcher v "")])))

(def age-conversion
  (merge
    (zipmap ["year" "y" "yr"] (repeat 12))
    (zipmap ["month" "moth" "mo" "m"] (repeat 1))
    (zipmap ["week" "wek" "wk" "w"] (repeat (/ 1 4.5)))
    (zipmap ["day" "d"] (repeat (/ 1 30)))
    (zipmap ["hour" "hr" "h"] (repeat (/ 1 (* 24 30))))))

(defn parse-double [x]
  (if x
    (try
      (Double/parseDouble x)  
      (catch Exception e
        nil))))

(defn match [matcher text]
  (.reset matcher text)
  (if (.find matcher) matcher))

(defn match-group [matcher group text]
  (when-let [m (match matcher text)]
    (.group m group)))

(defn extract-age [text & {:keys [default-unit] :or {default-unit nil}}]
  (when text
    (when-let [m (match (:age matchers) (.toLowerCase text))]
      (let [age (Double/parseDouble (.group m "age"))
            age-end (parse-double (.group m "end"))
            unit (or (match-group (matchers :age-unit) "unit" text)
                     (.group m "unity")
                     (.group m "unitx")
                     default-unit
                     "")
            unit-conversion (age-conversion 
                              (.replaceAll (.trim unit) "s$" ""))]
        (if unit-conversion
          (let [age (mean [age (or age-end age)])]
            (* unit-conversion age)))))))

(defonce ontology-trie
  (memoize
    (fn [prefix]
      (let [q ["SELECT * FROM ontology_synonyms WHERE prefix=?"
               prefix]]
        (text/chunker
          (for [s (query q)]
            (es.corygil.text.Synonym. (:id s) (:synonym s))))))))

(defn extract-ontology [prefix txt]
  (for [match (text/chunk (ontology-trie prefix) txt)]
    (:id match)))

(defn get-id! [table e-name]
  (let [q (-> (str "get-" (name table) "-id")
              keyword db/lookup-query)
        row (first (query [q e-name]))]
    (if-not row
      (do
        (insert! (name table) ["name"] [e-name])
        (get-id! table e-name)) 
      (:id row))))

(defn get-evidence-id! [name]
  (get-id! :evidence name))

(defn get-source-id! [name]
  (get-id! :source name))

(defonce age-term-id
  (->
    (sql/query db/spec "SELECT age_term_id();")
    first :age_term_id))

(defn extract-channel-age []
  (let [evidence-id (get-evidence-id! "text-mining")
        source-id (get-source-id! "Wren Lab")]
    (for [t (query ["SELECT * FROM channel_text"])
          :let [age (or 
                      (extract-age (:channel_text t))
                      (extract-age (:sample_text t)))]
          :when age]
      [age-term-id (:sample_id t) (:channel t)
       source-id evidence-id age nil])))

(defn annotate-channel-age! []
  (insert-term-channel!
    (extract-channel-age)))

(defn annotate-channel-with-ontology! [prefix]
  (insert-term-channel!
    (let [evidence-id (get-evidence-id! "text-mining")
          source-id (get-source-id! "Wren Lab")]
      (for [t (query ["SELECT * FROM channel_text"])
            term-id 
            (extract-ontology 
              prefix 
              (str (:channel_text t) " " (:sample_text t)))]
        [term-id (:sample_id t) (:channel t) 
         source-id evidence-id nil nil]))))

(def ursa-annotations
  (clojure.java.io/resource
    "data/manual_annotations_ursa.csv"))

(defn sample-accession-to-id [taxon-id]
  (into {}
        (map #(vector (:accession %) (:id %))
             (query [(db/lookup-query :sample-accession-map)
                     taxon-id]))))

(defn import-ursa! []
  (with-open [rdr (clojure.java.io/reader ursa-annotations)]
    (let [gsm-to-id (sample-accession-to-id 9606)
          evidence-id (get-evidence-id! "manual")
          source-id (get-source-id! "URSA")]
      (insert-term-channel!
        (for [line (line-seq rdr)
                :let [[gsm _ term] (.split line "\t")
                      term-id (first
                                (extract-ontology "BTO" term))
                      sample-id (gsm-to-id gsm)]
                :when (and term-id sample-id)]
          [term-id sample-id 1 
           source-id evidence-id nil 0.99])))))

(defn -main []
  (annotate-channel-with-ontology! "BTO")
  (annotate-channel-age!)
  (import-ursa!))
