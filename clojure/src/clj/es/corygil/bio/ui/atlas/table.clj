(ns es.corygil.bio.ui.atlas.table
  [:require
   [clojure.java.jdbc :as sql]
   [es.corygil.bio.db :as db]
   [es.corygil.bio.ui.atlas.cache :as c]
   [es.corygil.bio.ui.atlas.query :as q]])

(defn query [query & args]
  "Returns a Table from a SQL query."
  (let [rs (sql/query db/spec (cons query args) 
                      :identifiers identity
                      :as-arrays? true)] 
    (c/add! 
      {:columns (first rs)
       :rows (vec (rest rs))}))) 

(defn- render [table]
  [:table {:class "table table-striped table-hover display data-table"
           :cellspacing "0"
           :width "100%"
           :uuid (:uuid table)}
   [:thead
    [:tr
     (for [c (:columns table)]
       [:td c])]]])

(defn render-query [& args]
  (render (apply query args)))

(defn ajax [request]
  (let [params (request :params)
        draw (Integer/parseInt (params :draw))
        start (Integer/parseInt (params :start))
        order (get-in params [:order "0"])
        sort-col (Integer/parseInt (order :column))
        length (Integer/parseInt (params :length))
        table (c/lookup (params :uuid))
        rows ((if (= (:dir order) "asc") identity reverse)
              (sort-by #(% sort-col) 
                       (:rows table)))
        query (.toLowerCase (get-in params [:search :value]))
        filter-fn (fn [row]
                    (some #(.contains (.toLowerCase (str %)) query)
                          row))
        filtered-rows (if-not query rows
                        (filter filter-fn rows))]
    {:body
     {:draw draw
      :recordsTotal (count (:rows table))
      :recordsFiltered (count filtered-rows)
      :data 
      (take length (drop start filtered-rows))}})) 
