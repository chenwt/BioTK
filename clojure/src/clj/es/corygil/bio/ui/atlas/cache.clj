(ns es.corygil.bio.ui.atlas.cache
  (:require
    [clojure.core.cache :as c]))
 
(def cache
  (atom 
    (c/lru-cache-factory {} :threshold 25)))

(defn lookup [uuid] 
  (c/lookup @cache uuid))

(defn add! [item]
  (let [uuid (or (:uuid item) 
                 (str (java.util.UUID/randomUUID)))
        item (assoc item :uuid uuid)]
    (swap! cache assoc uuid item)
    (lookup uuid)))

