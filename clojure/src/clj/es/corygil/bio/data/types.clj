(ns es.corygil.bio.data.types)

(deftype Index [name index values])

(deftype Series [name index data])

(deftype Frame [name elements])
