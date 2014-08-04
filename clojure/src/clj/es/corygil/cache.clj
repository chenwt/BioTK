(ns es.corygil.cache
  (:refer-clojure :exclude [get])
  (:require
    [taoensso.carmine :as car :refer [wcar]]
    [clojure.tools.logging :as log]
    [clojure.core.cache :as c]))

(def cache 
  (atom (c/lru-cache-factory {} :threshold 128)))

(defn get [k]
  (c/lookup @cache k))

(defn add! [item & {:keys [extra-keys] :or {extra-keys []}}]
  (let [uuid (or (:uuid (meta item))
                 (str (java.util.UUID/randomUUID)))
        item (with-meta item {:uuid uuid})
        ks (cons uuid extra-keys)]
    (doseq [k ks]
      (swap! cache assoc k item))
    item))

;; redis-based cache below, not used, because it can't serialize
;; deftype-based types

; defaults to localhost
(def redis
  {:pool {} :spec {:db 1}})

(defmacro wcar* [& body]
  `(car/wcar redis ~@body))

;(def cache (atom (c/lru-cache-factory {} :threshold 25)))

(defn -get [k]
  (wcar*
    (car/get k)))

(defn -add! [item & {:keys [extra-keys] :or {extra-keys []}}]
  ; Gives an item a metadata UUID and adds it to the cache,
  ; keyed by the UUID and any extra-keys provided.
  (let [uuid (or (:uuid (meta item))
                 (str (java.util.UUID/randomUUID)))
        item (with-meta item {:uuid uuid})
        ks (cons uuid extra-keys)]
    (wcar*
      (doseq [k ks]
        (car/set k item)))
    item))


