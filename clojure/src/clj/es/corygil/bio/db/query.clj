(ns es.corygil.bio.db.query
  (:require
    [es.corygil.bio.db.core :refer [query]]))

(defn ->map [q]
  (->>
    (query [q] :as-arrays? true)
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
 
(defn ->scalars [q]
  (map first (->rows q)))

(def ?->frame nil)
