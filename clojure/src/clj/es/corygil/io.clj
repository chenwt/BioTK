(ns es.corygil.io
  (:import
    [org.apache.commons.compress.archivers.tar TarArchiveInputStream]
    [java.util.zip GZIPInputStream])
  (:require
    [clojure.tools.logging :as log]))

(defn gzip-reader [file]
  (clojure.java.io/reader
    (GZIPInputStream.
      (clojure.java.io/input-stream file)))) 

(defn tgz-extract [pattern input]
  (with-open [stream
              (TarArchiveInputStream.
                (GZIPInputStream.
                  (clojure.java.io/input-stream input))
                "UTF-8")]
    (.getNextEntry stream)
    (loop [files []]
      (let [entry (.getCurrentEntry stream)
            file
            (if (re-matches pattern (.getName entry))
              (let [size (.getSize entry)
                    buffer (byte-array size)
                    offset (atom 0)]
                (while (< @offset size)
                  (swap! offset
                         (fn [offset]
                           (+ offset
                              (.read stream buffer offset size)))))
                {:name (.getName entry)
                 :data (clojure.java.io/reader
                         (java.io.ByteArrayInputStream. buffer))}))]
        (if (.getNextEntry stream)
          (recur (if file (cons file files) files))
          files)))))

;; Cache for downloaded files

(def file-cache-dir 
  (.getAbsoluteFile
    (java.io.File. (System/getProperty "user.home")
      ".cache/BioTK/clj/")))

(.mkdirs file-cache-dir)

(defn base64-encode [x]
  (.encodeToString
    (java.util.Base64/getUrlEncoder)
    (.getBytes (str x))))

(def download-lock (Object.))

(defn download [url]
  (let [f (java.io.File. file-cache-dir 
                         (base64-encode url))]
    (if-not (.exists f)
      (locking download-lock 
        (log/info "Cache miss for" (str url))
        (.createNewFile f)
        (with-open [in (clojure.java.io/input-stream url)
                    out (clojure.java.io/output-stream f)]
          (clojure.java.io/copy in out)))
      (log/info "Cache hit for" (str url)))
    (clojure.java.io/input-stream f))) 
