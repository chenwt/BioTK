(ns es.corygil.bio.ui.table
  (:use
    [es.corygil.data.core :only [rows dims]])
  (:require
    [es.corygil.cache :as c]
    [es.corygil.bio.db.core :as db]
    [clojure.java.jdbc :as sql]))

(defn- render [table]
 [:table {:class "table table-striped table-hover display data-table"
           :cellspacing "0"
           :width "100%"
           :uuid (:uuid (meta table))}
   [:thead
    [:tr
     (for [c (.columns table)]
       [:td c])]]])

(defn render-query [q & args]
  (render (db/execute q args)))

(defn ajax [request]
  (let [params (request :params)
        draw (Integer/parseInt (params :draw))
        start (Integer/parseInt (params :start))
        order (get-in params [:order "0"])
        sort-col (Integer/parseInt (order :column))
        length (Integer/parseInt (params :length))
        table (c/get (params :uuid))
        rows ((if (= (:dir order) "asc") identity reverse)
              (sort-by #(% sort-col) 
                       (rows table)))
        query (.toLowerCase (get-in params [:search :value]))
        filter-fn (fn [row]
                    (some #(.contains (.toLowerCase (str %)) query)
                          row))
        filtered-rows (if-not query rows
                        (filter filter-fn rows))
        [nr nc] (dims table)]
    {:body
     {:draw draw
      :recordsTotal nr
      :recordsFiltered (count filtered-rows)
      :data 
      (take length (drop start filtered-rows))}})) 
