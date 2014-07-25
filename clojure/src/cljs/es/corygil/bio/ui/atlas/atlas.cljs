(ns es.corygil.bio.ui.atlas.atlas
  (:require
    [jayq.core :as jq])
  (:use 
    [jayq.core :only [document-ready $]]))

(jq/bind ($ "button") :click (fn [] (js/alert "Hi")))
;(document-ready (js/alert "hi"))
