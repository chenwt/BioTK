$(shell mkdir -p bin)

CC=gcc
CXX=g++
CFLAGS=$(shell pkg-config --cflags apophenia)
CXXFLAGS=$(CFLAGS)
CFLAGS+=-std=c11
CXXFLAGS+=-std=c++0x
LDFLAGS=$(shell pkg-config --libs apophenia)

EXECUTABLES=$(patsubst src/%.cpp, bin/%, $(wildcard src/*.cpp))
EXECUTABLES+=$(patsubst src/%.c, bin/%, $(wildcard src/*.c))
#EXECUTABLES+=$(patsubst script/%, bin/%, $(wildcard script/*))

build: $(EXECUTABLES)

.PHONY: build

bin/%: src/%.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

bin/%: src/%.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

#bin/%: script/%
#	cp $^ $@
