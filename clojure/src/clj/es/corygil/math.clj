(ns es.corygil.math)

(defn sum [xs]
  (reduce + 0 xs))

(defn mean [xs]
  (let [[n sum]
        (reduce (fn [[n sum] x]
                  [(inc n) (+ sum x)])
                [0 0] xs)]
    (if (> n 0)
      (/ sum n) 0)))
