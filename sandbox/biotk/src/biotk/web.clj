(ns biotk.web
  (:require
    [clojure.java.jdbc :as sql]
    [compojure.core :refer [defroutes GET POST]]
    [compojure.handler :as handler]
    [ring.adapter.jetty :as ring]
    [hiccup.core :as h]
    [hiccup.page :as page]
    [compojure.route :as route]))

(defn index []
  (page/html5
    [:head
     [:title "Hello world"]]
    [:body
     [:div {:id "content"} "hello world"]]))

(defroutes routes
  (GET "/" [] (index)))

(def application (handler/site routes))

(def db "postgresql://titan:5432/dev")

(defn start [port]
  (ring/run-jetty application {:port port :join? false}))

(prn (sql/query db ["select * from taxon limit 1"]))

(defn -main []
  (start 8080))
