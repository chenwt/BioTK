(ns sandbox.zoltan)

(use 'es.corygil.data.core :reload)

(defn -main []
  (let [df (read-csv "/home/gilesc/zoltan.csv" :name "zdata")
        control (mean (df (range 4) nil))]
    (prn (seq control)) 
    ;(doseq [g (groupby df (fn [s] (subs (.name s) 0 2)))] (prn g))
    ))
