# Minimal Ndless build, using the official SDK's native Zehn output.
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
	$(GENZEHN) --input $< --output $@ --name "Nspire Smoke 001"

clean:
	rm -f main.o $(EXE).elf $(EXE).tns

.PHONY: all clean
