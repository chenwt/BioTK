require 'jmf'
require 'tables/dsv'
require 'format/printf'
require 'stats/base/univariate'
require 'stats/base/multivariate'

NB. ******************************
NB.       Global settings 
NB. ******************************

NB. Float print precision
NB. (9!:11)3 doesnt work

NB. ******************************
NB.             I/O
NB. ******************************

NB. y is path to jmx file
map_jmx =: 3 : 0
  JFL map_jmf_ 'map';y;y;1
  SLEN =: 0}map, JINT
  NR =: 1}map, JINT
  NC =: 2}map, JINT
  HLEN =: 3 + ((SLEN % 8) * (NR + NC))
  unmap_jmf_ 'map'

NB.  JCHAR map_jmf_ 'map';y;y;1
NB.  IXSZ =: SLEN * (NR + NC)
NB.  header =: IXSZ {. (3*8) }. map
NB.  index =: ((IXSZ % SLEN), SLEN) $ header
NB.  columns =: NR }. index
NB.  index =: NR {. index
NB.  unmap_jmf_ 'map'

  JFL map_jmf_ 'map';y
  (NR, NC) $ HLEN }. map
)
writerow =: 3 : 0 
  (jpath '/dev/stdout') writerow y
:
  y writedsv (x;TAB;'')
)
tout =: writerow
terr =: 3 : 0 
  (jpath '/dev/stderr') writerow y
)

NB. ******************************
NB.       Linear algebra 
NB. ******************************

dot =: (+/ . *)

NB. ******************************
NB.          Statistics 
NB. ******************************

NB. y is 2D matrix, samples are rows, probes columns
qnorm =: 3 : 0
  ((/:"1 y) i."1 i.#|:y) { (mean (/:~"1 y))
)

NB. standardize over rows
NB. y is 2D input matrix
standardize =: 3 : 0
  (y -"1 (mean y)) %"1 (stddev y)
)

cor =: 3 : 0
  nobs =: 0}$y
  Xs =: standardize y
  ((|: Xs) dot Xs) % (nobs - 1)
)

topcor =: 3 : 0
  ((1}$y)-1) topcor y
:
  top =: (x + 1)
  |: }. (i.top) { |: \:"1 (cor y)
)

NB. ******************************
NB.         ML metrics
NB. ******************************

NB. x = gold standard
NB. y = predictions
precision =: 4 : 0 
  (#x) %~ +/ x = y
)


NB. ******************************
NB.          General 
NB. ******************************

uniq =: ~.

normalize =: % +/

counts=: (\: {:"1)@(~. ,. #/.~)

ncounts =: 3 : 0
  c =: counts y
  f =: 1{"1 c
  > (0}"1 c) ,. (normalize f)
)

ixof =: 4 : 0
  (x=,y) # (i.#y)
)

NB. isna =: 3 : 0
NB. 0 = y = y
NB. )
isna =: (128!:5)

countna =: (+/ @: isna)

argsort =: 3 : 0
  (/: y) i. i.#y
)

streq =: 4 : 0
  1 - */"1 x = y
)

NB. junk
NB. Xn=:((/:"1 X) i."1 i.#|:X) { (mean (/:~"1 X))
NB. Xt =: (?. 5 4 $ 10000) % 10000
