EXE := NspireSmoke_Run001
CC := nspire-gcc
LD := nspire-ld

all: $(EXE).tns

$(EXE).o: main.c
	$(CC) -Wall -Wextra -Os -marm -c $< -o $@

$(EXE).elf: $(EXE).o
	$(LD) $< -o $@ -Wl,--gc-sections

$(EXE).tns: $(EXE).elf
	genzehn --input $< --output $@.zehn --name "Nspire Smoke 001"
	make-prg $@.zehn $@
	rm -f $@.zehn

clean:
	rm -f $(EXE).o $(EXE).elf $(EXE).tns $(EXE).tns.zehn

.PHONY: all clean
