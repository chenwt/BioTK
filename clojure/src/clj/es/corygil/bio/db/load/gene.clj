(ns es.corygil.bio.db.load.gene
  (:require
    [es.corygil.bio.db.load.util :refer [defloader]]
    [clojure.tools.logging :as log]
    [es.corygil.bio.db.query :as ?]
    [es.corygil.bio.db.core :refer [insert!]]
    [es.corygil.io :refer [download gzip-reader tgz-extract] :reload true]))

(def taxonomy-url
  (java.net.URL.
    "ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"))

(def gene-url
  (java.net.URL.
    "ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz"))

(def species
  (set
    (get-in (load-file "config.clj")
            [:database :species])))

(defloader load-taxonomy! :taxon
  (insert! :taxon [:accession :name]
           (for [line
                   (line-seq
                     (:data
                       (first 
                         (tgz-extract #"names.dmp$" (download taxonomy-url)))))
                   :let [[taxon-id name _ type]
                         (map #(.trim %) (.split line "\\|"))
                         taxon-id (Integer/parseInt taxon-id)]
                   :when (and 
                           (= type "scientific name") 
                           (contains? species name))]
             [(str taxon-id) name]))
  (log/info "[taxon] - Load complete"))

(defn gene-field [x]
  (if-not (= x "-") x))

(defloader load-gene! :gene
  (let [taxon-ids 
        (?/->map "SELECT accession,id FROM taxon;")]
    (insert! :gene [:taxon_id :accession :symbol :name]
             (for [line (-> gene-url download gzip-reader line-seq rest)
                   :let [fields (.split (.trim line) "\t")
                         taxon-id (taxon-ids (first fields))
                         gene-id (second fields)
                         symbol (gene-field (nth fields 3))
                         name (gene-field (nth fields 11))]
                   :when taxon-id]
               [taxon-id gene-id symbol name]))
    (log/info "[gene] - Load complete")))
