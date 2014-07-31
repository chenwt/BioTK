(ns es.corygil.bio.db.load2
  (:use
    [clojure.java.io :only [reader input-stream]])
  (:import
    [org.postgresql.util PGobject])
  (:require
    [monger.core :as mg]
    [monger.collection :as mc]
    [clojure.java.jdbc :as sql]
    [clojure.data.json :as json]
    [es.corygil.bio.db.core :as db]))

(def species-list
    (set
  [ "Homo sapiens"
    "Mus musculus"
    "Rattus norvegicus"
    "Arabidopsis thaliana"
    "Saccharomyces cerevisiae"
    "Sus scrofa"
    "Escherichia coli"
    "Caenorhabditis elegans"
    "Bos taurus"
    "Danio rerio"
    "Zea mays"
    "Oryza sativa"
    "Halobacterium sp. NRC-1"
    "Gallus gallus"
    "Macaca mulatta"
    "Streptomyces coelicolor"
    "Mycobacterium tuberculosis"
    "Campylobacter jejuni"
    "Mycobacterium tuberculosis H37Rv"
    "Pimephales promelas"
    "Canis lupus familiaris"
    "Bacillus subtilis"
    "Daphnia magna"
    "Staphylococcus aureus"
    "Salmonella enterica subsp. enterica serovar Typhimurium"
    "Plasmodium falciparum"
    "Glycine max"
    "Synechocystis sp. PCC 680"
    "Streptococcus mutans UA159"
    "Xenopus laevis"
    "Oryza sativa Japonica Group"
    "Equus caballus"
    "Bacillus subtilis subsp. subtilis str. 168"
    "Aedes aegypti"
    "Haemophilus influenzae"]))

(def mongo-connection
  (mg/connect {:host "db.wrenlab.org"}))

(def mdb
  (mg/get-db mongo-connection "dev"))

(def insert-batch (partial mc/insert-batch mdb))

; ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
(defn insert-taxon! []
  (with-open [rdr (reader
                    (input-stream "/home/gilesc/data/taxonomy/names.dmp"))]
    (insert-batch "taxon"
                  (for [line (rest (line-seq rdr))
                        :let [fields (map #(.trim %)
                                          (.split line "\\|"))
                              taxon-name (second fields)]
                        :when (species-list taxon-name)]
                    {:_id (Integer/parseInt (first fields))
                     :name taxon-name}))))

(defn gzopen [path]
  (clojure.java.io/reader
    (java.util.zip.GZIPInputStream.
      (clojure.java.io/input-stream 
        path))))

(defn insert-gene! []
  (with-open [rdr (gzopen "/home/gilesc/gene_info.gz")]
    (let [taxa (set (map :_id (mc/find-maps mdb "taxon")))]
      (insert-batch "gene"
                    (for [line (rest (line-seq rdr))
                            :let [fields (.split line "\t")
                                  taxon-id (Integer/parseInt (first fields))
                                  gene-id (Integer/parseInt (second fields))]
                            :when (taxa taxon-id)]
                      {:_id gene-id :taxon taxon-id
                       :symbol (nth fields 10)
                       :name (nth fields 11)})))))

(defn parse-soft-attribute-line [line]
  (try
    (let [[k v]
          (.split 
            (second
              (.split line "_" 2))
            " = " 2)]
      [(keyword (.replaceAll k "_" "-")) v])
    (catch Exception _ nil)))

(defn parse-soft-data-line [line]
  (try
    (let [fields (.split line "\t")]
      [(first fields)
       (Double/parseDouble (second fields))])
    (catch Exception _ nil)))

(defn read-soft-element [lines]
  (let [[attr-lines table-lines] (split-with 
                                   #(not (.endsWith (.trim %) "_table_begin"))
                                   lines)
        table (into {} (filter identity
                            (map parse-soft-data-line 
                                 (drop 2 (drop-last table-lines)))))]
    (merge {:probe-data table}
           (into {}
                 (filter identity
                         (map parse-soft-attribute-line attr-lines))))))

(defn read-soft [path]
  (with-open [rdr 
              (gzopen "/data/public/ncbi/geo/platform/GPL96_family.soft.gz")]
    (let [elements (partition-by #(.startsWith % "^") (line-seq rdr))]
      (doseq [[header e] (partition 2 elements)]
        (println
          (read-soft-element e))))))

(defn -main []
  ;(insert-taxon!)
  ;(insert-gene!) 
  (read-soft nil)
  )
