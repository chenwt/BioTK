(ns es.corygil.bio.db.load
  (:refer-clojure :exclude [source])
  (:use
    korma.db
    [korma.core :exclude [queries]] 
    es.corygil.math
    es.corygil.bio.db.core)
  (:require
    [es.corygil.text :as text]))

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
      (text/chunker
        (for [t (select term
                        (with synonym
                          (fields :text))
                        (with ontology
                          (fields)
                          (where {:prefix prefix})))
              s (cons (:name t) (map :text (:synonym t)))]
          (es.corygil.text.Synonym. (:id t) s))))))

(defn extract-ontology [prefix txt]
  (for [match (text/chunk (ontology-trie prefix) txt)]
    (:id match)))

(defmacro defgetset [fn-name table]
  `(defn ~fn-name [name-field]
     (if-let [id 
              (select-scalar ~table 
                             (fields :id)
                             (where {:name name-field}))]
       id
       (do
         (insert ~table
                 (values {:name name-field}))
         (~fn-name name-field)))))

(defn get-evidence-id! [name]
  (if-let [id 
           (select-scalar evidence 
                          (fields :id)
                          (where {:name name}))]
    id
    (do
      (insert evidence
              (values {:name name}))
      (get-evidence-id! name))))

(defn get-source-id! [name]
  (if-let [id 
           (select-scalar source 
                          (fields :id)
                          (where {:name name}))]
    id
    (do
      (insert source
              (values {:name name}))
      (get-source-id! name))))

(defonce age-term-id
  (select-scalar term
                 (fields :term.id)
                 (join ontology)
                 (where
                   {:ontology.prefix "PATO" :term.name "age"})))


(defn insert-many [table rows & {:keys [chunk-size] :or {chunk-size 500}}]
  (doseq [cnk (partition-all chunk-size rows)]
    (insert table (values cnk))))

(defn annotate-channel-age! []
  (let [evidence-id (get-evidence-id! "text-mining")
        source-id (get-source-id! "Wren Lab")
        term-id age-term-id]
    (insert-many term-channel
                 (for [t (select channel-text) 
                       :let [age (or (extract-age (:channel_text t))
                                     (extract-age (:sample_text t)))]
                       :when age]
                   {:term_id term-id :sample_id (:id t) 
                    :channel (:channel t)
                    :source_id source-id :evidence_id evidence-id
                    :value age}))))

(defn annotate-channel-with-ontology! [prefix]
  (insert-many term-channel
               (let [evidence-id (get-evidence-id! "text-mining")
                     source-id (get-source-id! "Wren Lab")]
                 (for [t (select channel-text)
                       term-id (extract-ontology prefix 
                                                 (str (:channel_text t) " " (:sample_text t)))]
                   {:term_id term-id :sample_id (:id t) :channel (:channel t)
                    :source_id source-id :evidence_id evidence-id}))))

(defn -main []
  (annotate-channel-with-ontology! "BTO")
  (annotate-channel-age!)
  )
