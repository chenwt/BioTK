(ns es.corygil.bio.db.load.geo
  (:require 
    [es.corygil.bio.db.core :refer [insert! insert-one!]
     :reload true]
    [es.corygil.bio.db.query :as ?]
    [es.corygil.bio.io.soft :as soft]
    [es.corygil.io :refer [gzip-reader]]))

(defn load-soft! [file]
  (with-open [rdr (gzip-reader file)]
    (let [elements (rest (take 10 (soft/read rdr))) 
          platform (first elements)
          source-id (?/->key-id! :source 
                                 "Gene Expression Omnibus")
          taxon-map (?/->map "SELECT accession,id FROM taxon;")
          platform-id 
          (insert-one! :platform 
                       [:source_id :accession :name :manufacturer]
                       (cons source-id
                             (map (:attributes platform)
                                  [:geo-accession :title 
                                   :manufacturer])))
          probe-map
          (do
            (insert! :probe [:platform_id :accession]
                     (for [row (:table platform)]
                       [platform-id (first row)]))
            (?/->map 
              (format "SELECT accession,id FROM probe
                       WHERE platform_id=%s;" platform-id)))]
      (doseq [e (rest elements)
              :when (= (:type e) :sample)
              :let [attrs (:attributes e)
                    sample-id 
                    (insert-one! 
                      :sample 
                      [:platform_id :accession]
                      (cons platform-id
                            (map attrs [:geo-accession])))]]
        (doseq [[i ch] (map-indexed vector 
                                    (:channels attrs)) 
                :let [i (inc i)
                      taxon-id (taxon-map 
                                 (ch :taxid))]
                ;; FIXME: read all channels
                :when (and taxon-id (= i 1))]
          (insert-one! 
            :channel 
            [:taxon_id :sample_id :channel]
            [taxon-id sample-id i]
            :return-id? false)
          (insert! :probe-value
                   [:probe-id :sample-id :channel :value]
                   (for [[probe-accession value] (:table e)
                         :let [probe-id 
                               (probe-map probe-accession)]
                         :when (and probe-id value)]
                     [probe-id sample-id i value])))))))

(def soft-dir
  (java.io.File.
    "/data/public/ncbi/geo/soft/rna/"))

(defn load-geo! []
  (pmap load-soft!
        (filter #(.endsWith (str %) ".soft.gz")
                (.listFiles soft-dir))))

(def soft-file
  (java.io.File.
    "/data/ncbi/geo/soft/GPL7473_family.soft.gz"))

(defn -main []
  (load-geo!)
  )
