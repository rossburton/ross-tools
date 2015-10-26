all:

INSTALL_DIR ?= ${HOME}/bin

install:
	install -m 0755 $(shell git ls-files | grep -v Makefile) ${INSTALL_DIR}
