(ns es.corygil.bio.db.core
  (:use
    korma.db
    korma.core)
  (:require
    [clojure.java.jdbc :as sql]))

(defdb db
  (postgres {:db "dev"
             :user "gilesc"
             :host "titan"}))

(declare taxon gene platform sample channel ontology term synonym)

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

(defrecord Table [uuid name query rows columns])

(def spec
  (:database
    (load-file "config.clj")))

(defn view [view-name & {:keys [limit]}]
  (sql/query spec [(format "SELECT * FROM %s %s" 
                           (.replaceAll (name view-name) "-", "_")
                           (if limit (str "LIMIT " limit)))]
             :identifiers #(.replaceAll (.toLowerCase %) "_", "-")))
