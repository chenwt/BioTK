manpages=$(patsubst doc/man/%.rst,share/man/man1/%.1.gz,$(wildcard doc/man/*.rst))
$(shell mkdir -p share/man/man1)

all: $(manpages)

share/man/man1/%.1.gz: doc/man/%.rst
	rst2man.py $^ | gzip > $@
