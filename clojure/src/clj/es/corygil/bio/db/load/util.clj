(ns es.corygil.bio.db.load.util
  (:require
    [clojure.tools.logging :as log]
    [es.corygil.bio.db.query :as ?]))

(defn run-if-needed [fn-name table-or-query run]
  (let [needed? (if (keyword? table-or-query)
                  (?/table-empty? table-or-query)
                  (not (?/has-results? table-or-query))) 
        msg (if needed?
              "Load complete"
              "Skipped (already loaded)")]
    (when needed?
      (log/info (format "[%s] - Starting" fn-name))
      (run))
    (log/info (format "[%s] - %s" fn-name msg))))

(defmacro defloader [fn-name table-or-query & body]
  `(defn ~fn-name []
     (run-if-needed ~fn-name ~table-or-query 
                    (fn [] ~@body))))
