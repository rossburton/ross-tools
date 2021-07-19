all:

prefix = ${HOME}
bindir = ${prefix}/bin

install:
	mkdir -p ${bindir}
	for f in $(shell git ls-files); do \
		test -x $$f && install -m 0755 $$f ${bindir}/; \
	done
