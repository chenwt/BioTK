(ns es.corygil.data.core
  (:require
    [clojure.data.csv :as csv]
    [es.corygil.data.ops.scalar :as s]  
    [es.corygil.data.ops.reductions :as r]))

(def frame)

(def rm-nan 
  (partial filter #(not (Double/isNaN %))))

(defn drop-nth [n coll]
  (let [s (seq coll)]
    (concat
      (take n s)
      (rest s))))

; protocols

(defprotocol HasDimensions
  (dims [this]))

(defprotocol NDFrame
  (rows [this])
  (columns [this])
  (groupby [this f])
  (sortby-column [this col dir]))

(defprotocol ScalarOps
  (square [this])
  (cube [this])
  (sqrt [this]))

(defprotocol ReduceOps
  (sum [this])
  (mean [this])
  (variance [this])
  (stdev [this]))

(deftype Index [label values]
  HasDimensions
  (dims [this] [(count values)])

  clojure.lang.Seqable
  (seq [this]
    (seq values)))

(deftype Series [label index values]
  Object
  (toString [this] (format "%s - [%s]" label (count values)))

  HasDimensions
  (dims [this] [(count values)])

  ReduceOps
  (sum [this] (r/sum (rm-nan values)))
  (mean [this] (r/mean (rm-nan values)))
  (variance [this] (r/variance (rm-nan values)))
  (stdev [this] (r/stdev (rm-nan values)))

  clojure.lang.IFn
  (invoke [this ix]
    (if (seq? ix)
      (Series. label 
               (mapv #(nth (.values index) %) ix)
               (mapv #(aget values %) ix))
      (aget values ix)))

  clojure.lang.Seqable
  (seq [this] (seq values)))

(deftype GroupBy [label index frames]
  clojure.lang.Seqable
  (seq [this] (vals frames)))

(deftype Frame [label index data metadata]
  Object
  (toString [this] (apply format "%s - %sx%s" label (dims this)))

  clojure.lang.IObj
  (meta [_] metadata)
  (withMeta [_ m]
    (Frame. label index data m))

  clojure.lang.IFn
  (invoke [this xs ys]
    (let [[nx ny] (dims this)
          xs (or xs (range nx))
          ys (or ys (range ny))
          data (mapv (vec data) ys)
          ss (mapv #(% xs) data)]
      (Frame. label (mapv #(nth (.values index) %) xs) ss metadata)))
  (invoke [this y]
    (first
      (for [c data
            :when (= (.label c) y)]
        c)))

  HasDimensions
  (dims [this] [(-> data first dims first) (count data)])

  ReduceOps
  (sum [this] (Series. label (columns this) (map sum data)))
  (mean [this] (Series. label (columns this) (map mean data)))
  (variance [this] (Series. label (columns this) (map variance data)))
  (stdev [this] (Series. label (columns this) (map stdev data)))

  NDFrame
  (rows [this] (apply map vector data))
  (columns [this]
    (mapv #(.label %) data))
  (groupby [this f]
    (GroupBy. label index
              (into {}
                    (for [[k ss] (group-by f this)]
                      [k (Frame. k index ss {})]))))
  (sortby-column [this c dir]
    (assert (contains? (.columns this) c))
    (let [col-ix (.indexOf (.columns this) c)
          rs ((if (= dir :asc) identity reverse) 
                (sort-by #(% (inc col-ix))
                         (map cons (.values index)
                              (rows this))))]
      (frame (.columns this) (mapv rest rs)
        :label label 
        :index (Index. (.label index) (mapv first rs)))))

  clojure.lang.Seqable
  (seq [this] (seq data)))

(defn parse-field
  ([x default]
   (try
     (Integer/parseInt x)
     (catch Exception e
       (try 
         (Double/parseDouble x)
         (catch Exception e default)))))
  ([x] (parse-field x nil)))

(defn series [values & {:keys [index label]}]
  (let [index (or index (-> values count range vec))
        types (set (map type values))]
    (Series. label index 
             (if (= 1 (count types))
               (into-array values)
               (into-array (map str values))))))


; FIXME: implement index-col, and case where index object
; is givne instead of seq
(defn frame [columns rows & {:keys [label index index-col]
                             :or {label nil}}]
  (let [[index rows columns]
        (if (-> index-col nil? not)
          (throw (Exception. "Not implemented"))
          [(Index. nil 
                   (or index (-> rows count range vec)))
           rows columns])]
    (Frame. label index
            (doall
              (for [[n d] (map vector columns 
                               (apply map vector rows))]
                (series d :label n :index index)))
            {})))

; FIXME: use index-col param
(defn read-csv [path & {:keys [index-col label] :or {index-col 0}}]
  (with-open [rdr (clojure.java.io/reader path)]
    (let [data (doall (csv/read-csv rdr))
          columns (first data)
          rows (map (fn [row] (map #(parse-field % Double/NaN) row))
                    (rest data)) 
          ;index-name (nth (first rows) index-col)
          ;columns (drop-nth index-col (first rows)) 
          ;data (map (fn [row] (drop-nth index-col row))  (rest rows))
          ;index (Index. index-name (mapv #(nth % index-col) rows))
          ]
      (frame columns rows :label label))))
