PACKAGES=xmat
#DESTDIR=$(HOME)/.local
DESTDIR ?= $(HOME)/test
export DESTDIR

install: 
	mkdir -p $(DESTDIR)/bin
	@for pkg in $(PACKAGES) ; do \
		make -C $$pkg install ; \
	done

.PHONY: install
