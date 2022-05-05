all: scmp_run

scmp_run: scmp_run.c
	gcc -Wall -o $@ $^ $(shell pkg-config --cflags libseccomp)

clean:
	rm -f scmp_run

.PHONY: clean all
