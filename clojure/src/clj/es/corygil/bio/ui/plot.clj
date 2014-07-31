(ns es.corygil.bio.ui.plot
  (:use
    [es.corygil.data.core :only [rows columns]])
  (:require
    [es.corygil.cache :as c]))

(defrecord Series [name xs ys])

(def test-series
  (Series. :foo [1 2 3] [4 5 6]))

(defn- common [& {:keys [title x-label y-label height]
                 :or {title "title" x-label "X" 
                      y-label "Y" height 400}}]
  {:title title :x-label x-label :y-label y-label :height height})

(def default-args
  {:title "title" :x-label "X" :y-label "X" :height 400})

(defn render [plot]
  [:div {:class "plot" 
         :type (:type plot) 
         :uuid (:uuid (meta plot))}
   [:p {:class "loading"} "Loading data"]])

(defn scatter [frames & kwargs]
  (let [frames (vec frames)
        [x-label y-label] (take 2 (columns (first frames)))
        plot (c/add! 
               (merge {:type :scatter
                       :data (vec
                               (for [df frames]
                                 {:key (.label df)
                                  :values 
                                  (distinct
                                    (for [[id x y] (map (partial take 2) 
                                                     (rows df))]
                                      {:id id :x x :y y}))}))}
                      (merge default-args {:x-label x-label
                                           :y-label y-label})))]
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
    (c/get uuid)))
