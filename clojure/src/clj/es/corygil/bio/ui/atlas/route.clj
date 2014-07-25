(ns es.corygil.bio.ui.atlas.route
  (:require
    [compojure.core :refer [defroutes GET POST]]
    [compojure.handler :as handler]
    [compojure.route :as route]
    [ring.util.response :refer [response]]
    [ring.middleware.json :refer [wrap-json-response wrap-json-body]]
    [ring.adapter.jetty :as ring]

    [es.corygil.bio.ui.atlas.table :as t]  
    [es.corygil.bio.ui.atlas.plot :as p]
    [es.corygil.bio.ui.atlas.view :as v]))

(defroutes routes
  (GET "/" [] (v/index))
  (GET "/tutorial" [] (v/tutorial))
  (GET "/statistics" [] (v/statistics))
  (GET "/statistics/taxon/:taxon-id" [taxon-id]
       (v/taxon-statistics (Integer/parseInt taxon-id)))

  (GET "/control" [] (v/control nil))
  (POST "/control" request 
        (v/control (:params request)))

  (POST "/ajax/table" request (t/ajax request))
  (POST "/ajax/plot" request 
        (response (p/ajax request)))
  (route/resources "/")
  (route/not-found 
    "404: Page Not Found"))

(def application 
  (->
    (handler/site routes) 
    (wrap-json-response {:keywords? true})
    (wrap-json-body {:keywords? true :bigdecimals? true})))

(defn start [port]
  (ring/run-jetty application {:port port :join? false}))

(defn -main []
  (let [cfg (:ui (load-file "config.clj"))]
    (start (:port cfg))))
