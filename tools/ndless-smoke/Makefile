# Minimal native Ndless program. Follows the official Ndless SDK sample pipeline.
EXE = NspireSmoke_Run001
GCC = nspire-gcc
LD = nspire-ld
GENZEHN = genzehn

all: $(EXE).tns

main.o: main.c
	$(GCC) -Wall -Wextra -marm -Os -c $< -o $@

$(EXE).elf: main.o
	$(LD) $^ -o $@

$(EXE).tns: $(EXE).elf
	$(GENZEHN) --input $< --output $@.zehn --name "Nspire Smoke 001"
	make-prg $@.zehn $@
	rm -f $@.zehn

clean:
	rm -f main.o $(EXE).elf $(EXE).tns $(EXE).tns.zehn

.PHONY: all clean
