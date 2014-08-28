$(shell mkdir -p miniml matrix/probe matrix/gene matrix/taxon)

miniml/%.tar.gz :
	geo fetch -o miniml $*

matrix/probe/%.gz : miniml/%.tar.gz
	geo extract $^ | pigz > $@

# vim: set ft=make :
