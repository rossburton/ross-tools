all:

INSTALL_DIR ?= ${HOME}/bin

install:
	install -t ${INSTALL_DIR} -m 0755 $(shell git ls-files | grep -v Makefile)
