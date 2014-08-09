(ns es.corygil.bio.db.core
  (:refer-clojure :exclude [name])
  (:use
    es.corygil.data.core)
  (:import
    [es.corygil.data.core Frame]
    [org.postgresql.util PGobject]
    [com.mchange.v2.c3p0 ComboPooledDataSource])
  (:require
    [es.corygil.cache :as c]
    [clojure.data.json :as json]
    [clojure.java.jdbc :as sql]))

(def default-spec
  {:subprotocol "postgresql"
   :user "BioTK"
   :driver "org.postgresql.Driver"
   :subname "localhost:5432/dev"})

(def spec
  (merge
    default-spec
    (:database
      (load-file "config.clj"))))
 
(defn pool
  [spec]
  (let [cpds (doto (ComboPooledDataSource.)
               (.setDriverClass (:classname spec)) 
               (.setJdbcUrl (str "jdbc:" (:subprotocol spec) ":" (:subname spec)))
               (.setUser (:user spec))
               ;(.setPassword (:password spec))
               ;; expire excess connections after 30 minutes of inactivity:
               (.setMaxIdleTimeExcessConnections (* 30 60))
               ;; expire connections after 3 hours of inactivity:
               (.setMaxIdleTime (* 3 60 60)))] 
    {:datasource cpds}))

(def connection (pool spec))

(defn name [x]
  (.replaceAll (clojure.core/name x) "-" "_"))

(def query (partial sql/query connection))

(defn insert! [table columns rows] 
  (when (seq rows)
    (apply sql/insert! connection
           (name table) 
           (map name columns) 
           rows)))

(def insert-relations!
  (partial insert! :relation
           [:subject_id :object_id :predicate_id
            :source_id :evidence_id :value :probability]))

(def execute!  (partial sql/execute! connection))

(defn insert-one! [table columns row & 
                   {:keys [return-id?] :or {return-id? true}}]
  (let [q (format "INSERT INTO %s (%s) VALUES (%s) %s;"
                  (name table)
                  (->> columns (map name) (interpose ",") (apply str))
                  (apply str (interpose "," (repeat (count columns) "?")))
                  (if return-id? "RETURNING id" ""))
        q (cons q row)]
    (if return-id?
      (:id (first (query q)))
      (sql/execute! connection q))))

; Prepared queries

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
