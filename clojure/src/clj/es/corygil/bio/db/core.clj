(ns es.corygil.bio.db.core
  (:refer-clojure :exclude [name])
  (:use
    es.corygil.data.core)
  (:import
    [es.corygil.data.core Frame]
    [org.postgresql.util PGobject])
  (:require
    [es.corygil.cache :as c]
    [clojure.data.json :as json]
    [clojure.java.jdbc :as sql]))

(defn name [x]
  (.replaceAll (clojure.core/name x) "-" "_"))

(def spec
  (:database
    (load-file "config.clj")))

(def query (partial sql/query spec))

(defn insert! [table columns rows] 
  (when (seq rows)
    (apply sql/insert! spec 
           (name table) 
           (map name columns) 
           rows)))

(def insert-relations!
  (partial insert! :relation
           [:subject_id :object_id :predicate_id
            :source_id :evidence_id :value :probability]))

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
      (sql/execute! spec q))))

(def execute! (partial sql/execute! spec))

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
