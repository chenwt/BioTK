(ns es.corygil.bio.db.query
  (:require
    [yesql.core :refer [defqueries]]))

(def query-path 
  (.getFile (clojure.java.io/resource "sql/query.sql")))

(defqueries "sql/query.sql")
