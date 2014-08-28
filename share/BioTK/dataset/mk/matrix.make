$(shell mkdir -p miniml matrix/probe matrix/gene matrix/taxon)

miniml/%.tar.gz :
	geo fetch -o miniml $*

matrix/probe/%.gz : miniml/%.tar.gz
	geo extract $^ | pigz > $@

matrix/gene/%.gz : matrix/probe/%.gz
	geo collapse $^ | pigz > $@

# vim: set ft=make :
