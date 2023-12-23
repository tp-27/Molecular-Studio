#BEFORE RUNNING:  export LD_LIBRARY_PATH=. , swig -python molecule.i
CC = clang
CFLAGS = -std=c99 -pedantic -Wall
INC = /usr/include/python3.7
LIB = /usr/lib/python3.7/config-3.7m-x86_64-linux-gnu
PYTHON_VERSION = 3.7m

all: _molecule.so

libmol.so: mol.o
	$(CC) -shared mol.o -o libmol.so -lm

mol.o: mol.c mol.h
	$(CC) $(CLFAGS) -fpic -c mol.c -o mol.o

molecule_wrap.o: swig molecule_wrap.c
	$(CC) $(CLFLAGS) -fpic -c -I$(INC) molecule_wrap.c -o molecule_wrap.o

swig: molecule.i
	swig3.0 -python molecule.i

_molecule.so: libmol.so molecule_wrap.o
	$(CC) $(CFLAGS) -shared -L. -lmol -L$(LIB) -lpython$(PYTHON_VERSION) -dynamiclib -o _molecule.so molecule_wrap.o

clean:
	rm -f *.o *.so 
