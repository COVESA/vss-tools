#
# Demo build that uses the spec-generated C code to access the signal
# tree.
#


DEMO_VSS_VERSION=$(shell cat ../../VERSION)
CFLAGS= -O -Wall -fPIC -I.
TARGET=libvss.so
DEMO_TARGET=vss_demo
DEMO_OBJ=vss_demo.o


OBJ=vehicle_signal_specification.o
HDR=vehicle_signal_specification.h

all: ${TARGET} ${DEMO_TARGET}

${TARGET}: ${OBJ} vss_generated.h
	${CC} -shared ${CFLAGS} -o ${TARGET} ${OBJ}

${OBJ}: ${HDR}

${DEMO_TARGET}: ${DEMO_OBJ} vss_generated.h vss_generated_macro.h
	gcc -o ${DEMO_TARGET} ${DEMO_OBJ} -L. -lvss

vss_generated.h: ../../vss_rel_${DEMO_VSS_VERSION}.h
	cp ../../vss_rel_${DEMO_VSS_VERSION}.h ./vss_generated.h
	cp ../../vss_rel_${DEMO_VSS_VERSION}_macro.h ./vss_generated_macro.h


clean:
	rm -f ${OBJ} ${TARGET} ${DEMO_TARGET} ${DEMO_OBJ} vss_generated.h vss_generated_macro.h *~
