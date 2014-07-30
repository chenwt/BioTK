(ns es.corygil.data.ops.reductions
  (:use
    es.corygil.data.ops.scalar))

(defn sum [xs]
  (reduce + xs))

(defn mean [xs]
  (/ (sum xs) (count xs)))

(defn variance [xs]
  ; Unbiased sample variance w/ Bessel's correction
  (let [mu (mean xs)]
    (/ (sum 
         (map (fn [x] (square (- x mu))) xs))
       (dec (count xs))))) 

(defn stdev [xs]
  (sqrt (variance xs)))
