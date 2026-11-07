# Build and package the Run001 Ndless test program.
EXE = NspireSmoke_Run001
GCC = nspire-gcc
LD = nspire-ld
GENZEHN = genzehn

all: $(EXE).tns

main.o: main.c
	$(GCC) -Wall -Wextra -marm -Os -c $< -o $@

$(EXE).elf: main.o
	$(LD) $^ -o $@

$(EXE).zehn: $(EXE).elf
	$(GENZEHN) --input $< --output $@ --name "Nspire Smoke 001"

$(EXE).tns: $(EXE).zehn
	make-prg $< $@

clean:
	rm -f main.o $(EXE).elf $(EXE).zehn $(EXE).tns

.PHONY: all clean
