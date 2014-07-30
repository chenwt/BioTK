(ns es.corygil.bio.db.core
  (:refer-clojure :exclude [source])
  (:use
    es.corygil.data.core
    korma.db
    [korma.core :exclude [queries]])
  (:import
    [es.corygil.data.core Frame])
  (:require
    [es.corygil.cache :as c]
    [clojure.java.jdbc :as sql]))

(def spec
  (:database
    (load-file "config.clj")))

(def queries
  (let [dir (java.io.File. 
              (.getFile (clojure.java.io/resource "sql/query/")))]
    (into {}
          (for [f (.listFiles dir)
                :let [q-name (first (.split (.getName f) "\\."))]]
            [(keyword q-name) (slurp (.getPath f))]))))

(defn args-key [q args]
  (format "cache.sql.%s.%s" (name q) (hash args)))

(defn execute [q & {:keys [args order cache?] :or {args [] cache? false}}]
  (or (c/get (args-key q args))
      (let [rs (sql/query spec (vec (cons (queries q) args))
                          :as-arrays? true)
            columns (mapv name (first rs)) 
            rows (rest rs)
            table (frame columns rows :label (name q))]
        (let [table (if-not order
                      table
                      (let [[c dir] order]
                        (sortby-column table c order)))])
        (if-not cache? table
          (c/add! table :extra-keys [(args-key q args)])))))

(defdb db
  (postgres {:db "dev"
             :user "gilesc"
             :port 5432
             :host "db-pool"}))

(declare taxon gene platform sample channel ontology term synonym
         evidence source term-gene term-channel)

(defentity taxon
  (has-many gene)
  (has-many channel))

(defentity gene)

(defentity platform
  (has-many sample))

(defentity sample
  (has-many channel))
 
(defentity channel)

(defentity ontology
  (has-many term))

(defentity term
  (belongs-to ontology)
  (many-to-many synonym :term_synonym)
  (many-to-many gene :term_gene)
  (many-to-many channel :term_channel))
 
(defentity synonym
  (many-to-many term :term_synonym))

(defentity channel-text
  (table :channel_text))

(defentity evidence)

(defentity source)

(defentity term-channel
  (table :term_channel)
  (has-one evidence)
  (has-one source))

(defentity term-gene
  (table :term_gene)
  (has-one evidence)
  (has-one source))

(defrecord Table [uuid name query rows columns])

(defmacro select-scalar [& body]
  `(-> (select ~@body)
       first vals first))
 
(defn view [view-name & {:keys [limit]}]
  (sql/query spec [(format "SELECT * FROM %s %s" 
                           (.replaceAll (name view-name) "-", "_")
                           (if limit (str "LIMIT " limit)))]
             :identifiers #(.replaceAll (.toLowerCase %) "_", "-")))
