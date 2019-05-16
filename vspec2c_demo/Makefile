#
# Demo build that uses the spec-generated C code to access the signal
# tree.
#


#VSS_VERSION=$(cat ../../VERSION)
VSS_VERSION=2.0.0-alpha+005
CFLAGS=-DVSS_VERSION=\"${VSS_VERSION}\" -ggdb
TARGET=demo
OBJ=demo.o ../../vss_rel_${VSS_VERSION}.o
HDR=vss.h # Copied in from the master header so that the c


${TARGET}: ${OBJ}
	${CC} ${CFLAGS} -o ${TARGET} ${OBJ}

${OBJ}: ${HDR}

# Copy in the version-specific header file to the generic c file,
# allowing demo.c to do #include "vss.h" instead of
# #include "vss_rel_2.0.0-alpha+005.h", which may change at any time.
#
${HDR}: ../../vss_rel_${VSS_VERSION}.h
	cp $^ ${HDR}

clean:
	rm ${HDR} ${OBJ} ${TARGET} *~
