#
# Makefile to generate binary library
#

.PHONY: clean all binary

all: clean binary

binary:
	gcc -shared -o binarytool.so -fPIC binarytool.c

clean:
	rm -f binarytool.so
