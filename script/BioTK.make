#!/usr/bin/make -f

all: \
	bioconductor/GEOmetadb.sqlite \
	stanford/AILUN/done

SHELL=/bin/bash
AILUN_URL=ftp://ailun.stanford.edu/ailun/annotation/geo/
TAXA=9606 10116 10090

#foo:
#	echo $(patsubst %,ncbi/geo/matrix/gene/%.gz,\
#		$(shell cat stanford/AILUN/accessions.list))

$(shell mkdir -p \
	stanford/AILUN \
	bioconductor \
	ncbi/geo/miniml \
	ncbi/geo/matrix/{probe,gene} \
	ncbi/geo/matrix/taxon/{raw,normalized} \
	)

stanford/AILUN/accessions.list:
	curl -sl $(AILUN_URL) \
		| grep GPL \
		| cut -d. -f1 > $@

bioconductor/GEOmetadb.sqlite:
	curl -s http://gbnci.abcc.ncifcrf.gov/geo/GEOmetadb.sqlite.gz \
		| gzip -cd > $@

#stanford/AILUN/list:
#	curl -sl $(AILUN_URL) \
#		| head -10 \
#		| awk '{print "$(AILUN_URL)"$$0}' > $@

#stanford/AILUN/done: stanford/AILUN/list
#	multiget -P stanford/AILUN < $<
#	touch $@

stanford/AILUN/%.annot.gz:
	wget -P stanford/AILUN $(AILUN_URL)/$*.annot.gz

ncbi/geo/miniml/%.miniml.tpxz:
	geo-fetch -o ncbi/geo/miniml $*

ncbi/geo/matrix/probe/%.gz: ncbi/geo/miniml/%.miniml.tpxz
	geo-extract $^ | gzip > $@	

ncbi/geo/matrix/gene/%.gz: \
		stanford/AILUN/%.annot.gz ncbi/geo/matrix/probe/%.gz
	zcat $(word 2,$^) \
		| dm collapse <(zcat $< | cut -f1-2 | sed 1d) \
		| gzip > $@

		#$(patsubst %,ncbi/geo/matrix/gene/%.gz,\
		#	$(shell geo accessions -t $(1)))
		#

foo:
	echo $(lastword $(MAKEFILE_LIST))
