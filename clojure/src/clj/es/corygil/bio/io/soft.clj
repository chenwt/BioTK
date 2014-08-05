(ns es.corygil.bio.io.soft
  (:refer-clojure :exclude [read])
  (:require
    [es.corygil.io :refer [gzip-reader]]))

(defn parse-attribute-line [line]
  (try
    (let [[k v]
          (.split 
            (second
              (.split line "_" 2))
            " = " 2)]
      [(keyword (.replaceAll k "_" "-")) v])
    (catch Exception _ nil)))

(defn parse-data-line [line]
  (try
    (let [fields (.split line "\t")]
      [(first fields)
       (Double/parseDouble (second fields))])
    (catch Exception _ nil)))

(def read-table nil)
(defmulti read-table 
  (fn [type _] type)
  :default :default)

(defmethod read-table :sample [_ lines]
  (->>
    lines
    (map parse-data-line)
    (filter identity)
    (into {})))

(defmethod read-table :platform [_ lines]
  (map #(vec (.split % "\t")) lines))

(defmethod read-table :default [_ lines])

(defn read-channel-attributes [n attrs]
  {:channels
   (vec
     (for [i (range 1 (inc n))
           :let [suffix (str "-ch" i)]]
       (into {}
             (for [[k v] attrs
                   :when (.endsWith (name k) suffix)
                   :let [k (->>
                             (.split (name k) "-")
                             drop-last (interpose "-") (apply str) keyword)]]
               [k v])))) })

(defn read-attributes [lines]
  (let [attrs (->>
                lines
                (map parse-attribute-line)
                (filter identity)
                (into {}))
        groups 
        (group-by (fn [[k v]]
                    (boolean (re-find #"-ch[0-9]+$" (name k))))
                  attrs)
        [attrs ch-attrs] (map #(into {} (groups % [])) [false true])]
    (merge attrs
           (if-let [n (and (:channel-count attrs)
                           (Integer/parseInt (:channel-count attrs)))]
             (read-channel-attributes n ch-attrs)))))

(defn read-element [type lines]
  (let [[attr-lines table-lines] 
        (split-with 
          #(not (.endsWith (.trim %) "_table_begin"))
          lines)]
    [(read-table type 
                 (drop-last (drop 2 table-lines)))
     (read-attributes attr-lines)]))

(defrecord SOFTElement [type table attributes])

(defn read [rdr]
  (pmap (fn [[header lines]]
          (let [type (-> header
                         first (.split " = ") first 
                         (.toLowerCase) (.substring 1) 
                         keyword)
                [data attrs] (read-element type lines)]
            (SOFTElement. type data attrs)))
        (partition 2
                   (partition-by 
                     #(.startsWith % "^") 
                     (line-seq rdr)))))
