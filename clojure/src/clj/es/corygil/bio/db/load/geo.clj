(ns es.corygil.bio.db.load.geo
  (:require 
    [clojure.tools.logging :as log]
    [es.corygil.bio.db.core :refer [insert! insert-one!]]
    [es.corygil.bio.db.query :as ?]
    [es.corygil.bio.io.soft :as soft]
    [es.corygil.io :refer [gzip-reader]]))

(defn load-samples! [file]
  (with-open [rdr (gzip-reader file)]
    (let [elements (rest (soft/read rdr))
          platform (first elements)
          platform-id (?/->scalar "SELECT id FROM platform WHERE accession=?" 
                                  (get-in platform [:attributes :geo-accession]))
          taxon-map (?/->map "SELECT accession,id FROM taxon;")]
      (with-open [wtr (clojure.java.io/writer (str "/home/gilesc/tmp3/" platform-id))]
        (when-let [probe-map
                   (?/->map 
                     (format "SELECT accession,id FROM probe
                             WHERE platform_id=%s;" platform-id))]
          (doseq [e (rest elements)
                  [i ch] (map-indexed vector 
                                      (get-in e [:attributes :channels]))
                  :let [i (inc i)
                        sample-id (?/->scalar "SELECT id FROM sample WHERE accession=?" 
                                              (get-in e [:attributes :geo-accession]))]
                  :when (= i 1)]
            (doseq [[probe-accession value] (:table e)
                    :let [probe-id 
                          (probe-map probe-accession)]
                    :when (and probe-id value)]
              (->>
                [probe-id sample-id i (str value "\n")]
                (interpose "\t")
                (apply str)
                (.write wtr)))))))))

(comment
  (insert! :probe-value
           [:probe-id :sample-id :channel :value]
           (for [[probe-accession value] (:table e)
                 :let [probe-id 
                       (probe-map probe-accession)]
                 :when (and probe-id value)]
             [probe-id sample-id i value]))
  )

(defonce source-id
  (?/->key-id! :source "Gene Expression Omnibus"))

(defn load-platform! [file]
  (with-open [rdr (gzip-reader file)]
    (let [elements (rest (soft/read rdr))
          platform (first elements)
          taxon-map (?/->map "SELECT accession,id FROM taxon;")
          platform-id 
          (insert-one! :platform 
                       [:source_id :accession :name :manufacturer]
                       (cons source-id
                             (map (:attributes platform)
                                  [:geo-accession :title 
                                   :manufacturer])))]
      (insert! :probe [:platform_id :accession]
                   (for [row (:table platform)]
                     [platform-id (first row)]))
      (doseq [e (rest elements)
              :when (= (:type e) :sample)
              :let [attrs (assoc (:attributes e)
                                 :channel-count
                                 (Integer/parseInt 
                                   (get-in e [:attributes :channel-count])))
                    sample-id 
                    (insert-one! 
                      :sample 
                      [:platform_id :accession
                       :name :description :type :channel-count]
                      (cons platform-id
                            (map attrs 
                                 [:geo-accession :title :description
                                  :type :channel-count])))]]
        (doseq [[i ch] (map-indexed vector 
                                    (get-in e [:attributes :channels]))
                :let [i (inc i)
                      taxon-id (taxon-map (ch :taxid))]
                ;; FIXME: read all channels
                :when (and taxon-id (= i 1))]
          (insert-one! 
            :channel 
            [:taxon_id :sample_id :channel
             :source-name :characteristics :molecule :label
             :treatment-protocol :extract-protocol :label-protocol]
            (concat [taxon-id sample-id i]
                    (map ch
                         [:source-name :characteristics :molecule :label
                          :treatment-protocol :extract-protocol 
                          :label-protocol]))
              :return-id? false))))))

(def soft-dir
  (java.io.File.
    "/data/public/ncbi/geo/soft/rna/"))

(defn map-over-soft [f]
  (pmap (fn [file]
          (try
            (f file)
            (catch Exception e
              (log/error e))))
        (filter #(.endsWith (str %) ".soft.gz")
                (.listFiles soft-dir))))

(def probe-map-dir
  (java.io.File.
    "/data/public/ncbi/geo/annotation/AILUN/"))

(defn load-mapping! [file])

(defn load-probe-mappings! []
  (let [gene-map (?/->map "SELECT accession,id FROM gene")]
    (doseq [accession (?/->scalars "SELECT accession FROM platform")
            :let [file (java.io.File. probe-map-dir 
                                      (str accession ".annot.gz"))]
            :when (and (.exists file))]
      (let [probe-map (?/->map 
                        "SELECT probe.accession,probe.id FROM probe
                        INNER JOIN platform
                        ON probe.platform_id=platform.id
                        WHERE platform.accession=?" accession)]
        (with-open [rdr (gzip-reader file)]
          (log/info accession)
          (insert! :probe_gene [:probe_id :gene_id]
                   (for [line (line-seq rdr)
                         :let [fields (.split line "\t")
                               [probe gene] (take 2 fields)
                               probe-id (probe-map probe)
                               gene-id (gene-map gene)]
                         :when (and probe-id gene-id)]
                     [probe-id gene-id])))))))

(defn -main []
  ;(map-over-soft load-platform!)
  (map-over-soft load-samples!)

  )


