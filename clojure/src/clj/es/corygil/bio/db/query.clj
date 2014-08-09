(ns es.corygil.bio.db.query
  (:refer-clojure :exclude [name])
  (:require
    [es.corygil.bio.db.core :refer [query name]]))

(defn ->map [q & args]
  (->>
    (query (cons q args) :as-arrays? true)
    rest
    (into {})))

(defn kv-map [table]
  (->map
    (format "SELECT value,id FROM %s" (name table))))

(defn ->key-id! [table value]
  (or
    (-> 
      [(format "SELECT id FROM %s WHERE value=?" 
               (name table)) (name value)]
      query first :id)
    (->
      [(format "INSERT INTO %s (value) VALUES (?) RETURNING id;"
               (name table)) (name value)]
      query first :id)))

(defn ->rows [q & args]
  (rest 
    (query (cons q args)
           :as-arrays? true)))
 
(defn ->scalars [q & args]
  (map first (apply ->rows q args)))

(defn ->scalar [q & args]
  (ffirst (apply ->rows q args)))

(def ?->frame nil)

(defn has-results? [q & args]
  (seq
    (query (cons q args))))

(defn table-empty? [table]
  (->> table
       name
       (format "SELECT * FROM %s LIMIT 1;")
       has-results? not))
