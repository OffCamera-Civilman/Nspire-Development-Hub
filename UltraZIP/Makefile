# UltraZIP 001 - same Ndless packaging sequence as the working smoke build.
GCC = nspire-gcc
LD = nspire-ld
GENZEHN = genzehn
CFLAGS = -Wall -Wextra -Os -marm -std=c99 -Ivendor/miniz
LDFLAGS = -Wl,--nspireio,--gc-sections
MINIZ = vendor/miniz/miniz.o vendor/miniz/miniz_zip.o vendor/miniz/miniz_tinfl.o vendor/miniz/miniz_tdef.o
OBJS = src/ultrazip.o src/ndless_compat.o $(MINIZ)

all: UltraZIP_001.tns

src/ndless_compat.o: src/ndless_compat.c
	$(GCC) $(CFLAGS) -c $< -o $@

src/ultrazip.o: src/ultrazip.c
	$(GCC) $(CFLAGS) -c $< -o $@

vendor/miniz/%.o: vendor/miniz/%.c
	$(GCC) $(CFLAGS) -c $< -o $@

UltraZIP_001.elf: $(OBJS)
	$(LD) $^ -o $@ $(LDFLAGS)

UltraZIP_001.tns: UltraZIP_001.elf
	$(GENZEHN) --input $< --output $@ --name "UltraZIP 001"

clean:
	rm -f $(OBJS) UltraZIP_001.elf UltraZIP_001.tns

.PHONY: all clean
