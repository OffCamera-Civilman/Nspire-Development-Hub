GCC = nspire-gcc
LD = nspire-ld
GENZEHN = genzehn
CFLAGS = -Wall -Wextra -Os -marm -std=c99 -Ivendor/miniz
OBJS = src/ultrazip.o vendor/miniz/miniz.o vendor/miniz/miniz_zip.o vendor/miniz/miniz_tinfl.o vendor/miniz/miniz_tdef.o

all: UltraZIP_001.tns

src/ultrazip.o: src/ultrazip.c
	$(GCC) $(CFLAGS) -c $< -o $@

vendor/miniz/%.o: vendor/miniz/%.c
	$(GCC) $(CFLAGS) -c $< -o $@

UltraZIP_001.elf: $(OBJS)
	$(LD) $(OBJS) -o $@ -Wl,--nspireio,--gc-sections

UltraZIP_001.tns: UltraZIP_001.elf
	$(GENZEHN) --input $< --output $@.zehn --name "UltraZIP"
	make-prg $@.zehn $@
	rm -f $@.zehn

clean:
	rm -f $(OBJS) UltraZIP_001.elf UltraZIP_001.tns UltraZIP_001.tns.zehn

.PHONY: all clean
