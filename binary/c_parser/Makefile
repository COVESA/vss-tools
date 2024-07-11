#
# Makefile to generate binary library
#

.PHONY: clean all binary

all: clean binary

binary:
	gcc testparser.c cparserlib.c -o ctestparser

clean:
	rm -f ctestparser
