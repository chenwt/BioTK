(ns es.corygil.data)

(defprotocol HasDimensions
  (dims [this]))

(deftype Index [name values]
  HasDimensions
  (dims [this] [(count values)])

  clojure.lang.Seqable
  (seq [this]
    (seq values)))

(deftype Series [name index values]
  HasDimensions
  (dims [this] [(count values)])

  clojure.lang.Seqable
  (seq [this]
    (seq values)))

(deftype Frame [name index columns data]
  HasDimensions
  (dims [this] [(count index) (count columns)]))
