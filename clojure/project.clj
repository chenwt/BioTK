(defproject es.corygil/bio "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :source-paths ["src/clj" "src/cljs"]
  :plugins [[lein-cljsbuild "1.0.3"]
            [lein-ring "0.8.11"]]
  :dependencies [[org.clojure/clojure "1.6.0"]
                 [org.clojure/java.jdbc "0.3.3"]
                 [org.clojure/core.cache "0.6.3"]
                 [org.clojure/data.csv "0.1.2"]
                 [org.clojure/data.json "0.2.5"]
                 [com.novemberain/monger "2.0.0"]
                 [yesql "0.4.0"]
                 [korma "0.3.2"]
                 [com.taoensso/carmine "2.6.2"]
                 [com.aliasi/lingpipe "4.0.1"]
                 [postgresql "9.1-901.jdbc4"]
                 [ring/ring-jetty-adapter "1.2.1"]
                 [ring/ring-json "0.3.1"]
                 [compojure "1.1.6"]
                 [hiccup "1.0.4"]
                 [aysylu/loom "0.5.0"]

                 [org.clojure/clojurescript "0.0-2197"]
                 [jayq "2.5.1"]
                 
                 ]
  ; Ring
  :ring {:port 5678
         :auto-refresh? true
         :handler es.corygil.bio.ui.route/application}
  :repl-options {:init-ns user ;es.corygil.bio.db.load2
                 ;:init (-main)
                 }
  ; ClojureScript
  ;:hooks [leiningen.cljsbuild]
  ;:cljsbuild {:builds
  ;           [{
  ;             :source-paths ["src/cljs/es/corygil/bio/ui/atlas"]
  ;             :compiler 
  ;             {:output-to "resources/public/atlas.js"
  ;              :optimizations :whitespace
  ;              :externs ["resources/public/bower/jquery/dist/jquery.js"]
  ;              :pretty-print true}}]}
  )
