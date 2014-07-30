(ns es.corygil.text)

(def tokenizer-factory
  (com.aliasi.tokenizer.IndoEuropeanTokenizerFactory/INSTANCE))

(defrecord Synonym [term-id text])
(defrecord Match [id start end])
 
(defn chunker [synonyms]
  (let [d (com.aliasi.dict.MapDictionary.)]
    (doseq [s synonyms]
      (.addEntry d (com.aliasi.dict.DictionaryEntry.
                     (:text s) (str (:term-id s)) 1.0)))
    (com.aliasi.dict.ExactDictionaryChunker. 
      d tokenizer-factory
      true false)))

(defn chunk [chunker text]
  (when text
    (sort-by #(- (:start %) (:end %))
             (for [m (.chunk chunker text)] 
               (Match. (Integer/parseInt (.type m)) 
                       (.start m) (.end m))))))
