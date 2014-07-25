(ns es.corygil.bio.ui.atlas.plot
  (:require
    [es.corygil.bio.ui.atlas.cache :as c]))

(defrecord Series [name xs ys])

(def test-series
  (Series. :foo [1 2 3] [4 5 6]))

(defn- common [& {:keys [title x-label y-label]
                 :or {title "title" x-label "X" y-label "Y"}}]
  {:title title :x-label x-label :y-label y-label})

(defn render [plot]
  [:div {:class "plot" :type (:type plot) :uuid (:uuid plot)}
   [:p {:class "loading"} "Loading data"]])

(defn scatter [data & kwargs]
  ; 'data' is a collection of Series types
  (let [plot (c/add! 
               (merge {:type :scatter
                       :data (for [s data]
                        {:key (:name s) :values
                        (mapv (fn [x y] {:x x :y y}) (:xs s) (:ys s))})}
                      (apply common kwargs)))]
    (render plot)))

(defn bar [data & kwargs]
  ; 'data' is a Series
  (let [plot (c/add!
               (merge (apply common kwargs)
                      {:type :bar
                       :data [{:key (:name data)
                              :values (map vector (:xs data) (:ys data))}]}))]
    (render plot)))

(defn ajax [request]
  (let [uuid (get-in request [:params :uuid])]
    (c/lookup uuid)))
