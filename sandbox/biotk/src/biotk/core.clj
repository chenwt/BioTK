(ns biotk.core)

(defn foo
  "I don't do a whole lot."
  [x]
  (println x "Hello, World!"))

(use '[clojure.tools.nrepl.server :only (start-server stop-server)])

(defn -main []
  (defonce server (start-server :port 7888)))

(foo 5)

