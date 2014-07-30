(ns es.corygil.bio.ui.view
  (:require
    [hiccup.page :refer [html5 include-js include-css]]
    [hiccup.core :as h]
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
        [:li [:a {:href "/query/tisue"} "Tissue"]]]]

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

(defpage index []
  [:div 
    (p/scatter [p/test-series]) 
    ;(p/bar p/test-series)
   ])

(defpage statistics []
  (t/render-query "SELECT * FROM channel_data_by_taxon;"))

(defpage taxon-statistics [taxon-id]
  (t/render-query 
    "SELECT cd.* FROM channel_data_by_accession cd
    INNER JOIN taxon 
    ON taxon.name=cd.\"Species\"
    WHERE taxon.id=?;" taxon-id))

(defstatic tutorial "tutorial")

(defpage control [params]
  (prn params)
  [:form {:id "control" :method "post"}
    [:h3 "Database"]
   [:input {:type "submit" :name "action" :value "MyButton"}]
   [:input {:type "submit" :name "action" :value "MyButton2"}]])
