all:

prefix = ${HOME}
bindir = ${prefix}/bin

install:
	mkdir -p ${bindir}
	for f in $(shell git ls-files | grep -v Makefile); do \
		install -m 0755 $$f ${bindir}/; \
	done
