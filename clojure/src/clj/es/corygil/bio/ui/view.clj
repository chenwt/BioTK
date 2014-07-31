(ns es.corygil.bio.ui.view
  (:require
    [hiccup.page :refer [html5 include-js include-css]]
    [hiccup.core :as h]
    [clojure.java.jdbc :as sql]
    [es.corygil.bio.db.core :as db]
    [es.corygil.bio.ui.table :as t]
    [es.corygil.bio.ui.plot :as p]))

(def TITLE "AGE Atlas")

(def NAV
  [:nav {:class "navbar navbar-default" :role "navigation"}
   [:div {:class "container-fluid"}
    [:div {:class "navbar-header"}]
    [:a {:class "navbar-brand" :href "/"} TITLE]
    [:div {:class "collapse navbar-collapse"}
     [:ul {:class "nav navbar-nav"}

      [:li {:class "dropdown"}
       [:a {:href "#" :class "dropdown-toggle" :data-toggle "dropdown"} 
        "Query" 
        [:b {:class "caret"}]]
       [:ul {:class "dropdown-menu"}
        [:li [:a {:href "/query/tissue"} "Tissue"]]]]

      [:li [:a {:href "/tutorial"} "Tutorial"]]

      [:li {:class "dropdown"}
       [:a {:href "#" :class "dropdown-toggle" :data-toggle "dropdown"}
        "About"
        [:b {:class "caret"}]]
       [:ul {:class "dropdown-menu"}
        [:li [:a {:href "/statistics"} "Database statistics"]]
        [:li [:a {:href "/changelog"} "Changelog"]]]]

      [:form {:class "navbar-form navbar-left" :method "post" 
              :action "/search" :role "search"}
       [:div {:class "form-group"}
        [:input {:id "quick-search" :name "query" :type "text"
                 :class "form-control" 
                 :placeholder "Gene symbol, Entrez ID"}]]
       [:button {:class "btn btn-default" :type "submit"} "Search"]]]]]])

(def JS
  (mapv (partial include-js)
        (concat
         (map (partial format "/bower/%s.js")
              ["jquery/dist/jquery.min"
               "bootstrap/dist/js/bootstrap.min"
               "datatables/media/js/jquery.dataTables.min"
               "datatables-tabletools/js/dataTables.tableTools"
               "datatables/examples/resources/bootstrap/3/dataTables.bootstrap"
               "d3/d3.min"
               "nvd3/nv.d3.min"])
          ["/atlas.js"
           "/atlas.table.js"
           "/atlas.plot.js"])))

(def CSS
  (mapv (partial include-css)
       (concat
         (map (partial format "/bower/%s.css")
              ["bootstrap/dist/css/bootstrap.min"
               "datatables/examples/resources/bootstrap/3/dataTables.bootstrap"
               "datatables-tabletools/css/dataTables.tableTools"
               "nvd3/src/nv.d3"])
         ["/atlas.css"])))

(defn render-page [content & {:keys [title] :or {title TITLE}}]
  (html5
    [:head
     (concat JS CSS [[:title title]])]
    [:body
     NAV
     [:div {:class "container" :id "content"} 
      [:div {:class "row"}
       content]]]))

(defn static-content [name]
  (slurp
    (clojure.java.io/resource 
      (format "ui/content/%s.html" name))))

(defmacro defpage [name args & body]
  `(def ~name
     (fn [~@args]
       (render-page 
         (do ~@body)))))

(defmacro defstatic [name resource]
  (let [data (static-content resource)]
    `(def ~name 
       (constantly (render-page ~data)))))

(comment
  (.createArrayOf (sql/get-connection db/spec)
                                   "varchar"
                                   (into-array String ["heart"])))
(defpage index []
  [:div 
    ;(p/scatter [p/test-series]) 
    ;(p/bar p/test-series)
   ])

(defpage statistics []
  (t/render-query :channel-data-by-taxon))

(defpage taxon-statistics [taxon-id]
  (t/render-query :channel-data-for-taxon taxon-id))

(defstatic tutorial "tutorial")

(defpage control [params]
  [:form {:id "control" :method "post"}
    [:h3 "Database"]
   [:input {:type "submit" :name "action" :value "MyButton"}]
   [:input {:type "submit" :name "action" :value "MyButton2"}]])

(def default-tissues ["heart" "lung" "liver"])

(defpage plot-gene [gene-id]
  [:div
   (p/scatter 
     (for [tissue default-tissues]
       (db/execute :gene-expression-in-tissue 
                   :cache? true
                   :args [gene-id tissue gene-id])))])

(defpage query-tissue [])

(defpage query-tissue-for-taxon [taxon-id]
  [:div
   [:h3 "Select a species:"]
   (t/render
     (db/execute :term-channel-count :args ["BTO"] :cache? true)
     :link-format (format "/plot/tissue/%s/{1}" taxon-id))])

(defpage plot-tissue [taxon-id tissue-id]
  [:h1
   "Not implemented"])

(defpage quick-search [q]
  (t/render
    (db/execute :query-gene :args [q] :cache? true)
    :link-format "/plot/gene/{0}"))
