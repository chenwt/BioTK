(ns es.corygil.bio.db.core
  (:refer-clojure :exclude [source])
  (:use
    es.corygil.data.core
    korma.db
    [korma.core :exclude [queries]])
  (:import
    [es.corygil.data.core Frame]
    [org.postgresql.util PGobject])
  (:require
    [es.corygil.cache :as c]
    [clojure.data.json :as json]
    [clojure.java.jdbc :as sql]))

;; http://hiim.tv/clojure/2014/05/15/clojure-postgres-json/

(extend-protocol sql/ISQLValue
  clojure.lang.IPersistentMap
  (sql-value [value]
    (doto (PGobject.)
      (.setType "json")
      (.setValue (json/write-str value)))))

(extend-protocol sql/IResultSetReadColumn
  PGobject
  (result-set-read-column [pgobj metadata idx]
    (let [type  (.getType pgobj)
          value (.getValue pgobj)]
      (case type
        "json" (json/read-str value)
        :else value))))

(def spec
  (:database
    (load-file "config.clj")))

(def query-dir 
  (java.io.File. 
    (.getFile (clojure.java.io/resource "sql/query/"))))

(defn lookup-query [q-name]
  (let [f (java.io.File. query-dir 
                         (str (name q-name) ".sql"))]
    (if (.exists f)
      (slurp (.getPath f)))))

(def queries lookup-query)

(defn args-key [q args]
  (format "cache.sql.%s.%s" (name q) (hash args)))

(defn execute [q & {:keys [args order cache?] :or {args [] cache? false}}]
  (or (c/get (args-key q args))
      (let [rs (sql/query spec (vec (cons 
                                      (or (queries q)
                                          (format "SELECT * FROM %s;"
                                                  (.replaceAll (name q)
                                                               "-" "_")))
                                          args))
                          :identifiers identity
                          :as-arrays? true)
            columns (mapv name (first rs)) 
            order (or order [(first columns) :asc])
            rows (rest rs)
            table (frame columns rows :label (name q))]
        (let [table (if-not order
                      table
                      (let [[c dir] order]
                        (sortby-column table c order)))]
          (if-not cache? table
            (c/add! table :extra-keys [(args-key q args)]))))))
