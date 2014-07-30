(ns es.corygil.bio.ui.route
  (:require
    [compojure.core :refer [defroutes GET POST]]
    [compojure.handler :as handler]
    [compojure.route :as route]
    [ring.util.response :refer [response]]
    [ring.middleware.json :refer [wrap-json-response wrap-json-body]]
    [ring.adapter.jetty :as ring]

    [es.corygil.bio.ui.table :as t]  
    [es.corygil.bio.ui.plot :as p]
    [es.corygil.bio.ui.view :as v]))

(defroutes routes
  (GET "/" [] (v/index))
  (GET "/tutorial" [] (v/tutorial))
  (GET "/statistics" [] (v/statistics))
  (GET "/statistics/taxon/:taxon-id" [taxon-id]
       (v/taxon-statistics (Integer/parseInt taxon-id)))
  (GET "/plot/gene/:gene-id" [gene-id]
       (v/plot-gene (Integer/parseInt gene-id))) 

  (GET "/query/tissue" []
       (v/query-tissue))

  (GET "/control" [] (v/control nil))
  (POST "/control" request 
        (v/control (:params request)))

  (POST "/ajax/table" request (t/ajax request))
  (POST "/ajax/plot" request 
        (response (p/ajax request)))
  (route/resources "/")
  (route/not-found 
    "404: Page Not Found"))

(defn- log [msg & vals]
  (let [line (apply format msg vals)]
    (locking System/out (println line))))

(defn wrap-request-logging [handler]
  (fn [{:keys [request-method uri] :as req}]
    (let [start  (System/currentTimeMillis)
          resp   (handler req)
          finish (System/currentTimeMillis)
          total  (- finish start)]
      (log "request %s %s (%dms)" request-method uri total)
      resp)))

(def application 
  (->
    (handler/site routes) 
    wrap-request-logging
    (wrap-json-response {:keywords? true})
    (wrap-json-body {:keywords? true :bigdecimals? true})))

(defn start [port]
  (ring/run-jetty application {:port port :join? false}))

(defn -main []
  (let [cfg (:ui (load-file "config.clj"))]
    (start (:port cfg))))
