all:

prefix = ${HOME}
bindir = ${prefix}/bin

install:
	mkdir --parents ${bindir}
	for f in $(shell git ls-files | grep -v Makefile); do \
		install -m 0755 $$f ${bindir}/`basename $$f .py`; \
	done
