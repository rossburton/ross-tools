all:

prefix = ${HOME}
bindir = ${prefix}/bin

install:
	mkdir --parents ${bindir}
	install -m 0755 $(shell git ls-files | grep -v Makefile) ${bindir}
