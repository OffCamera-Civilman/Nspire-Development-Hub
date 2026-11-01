# UltraGBA

Target: TI-Nspire CX II CAS, OS 6.2.0.333, using Ndless.

## Baseline
- Upstream candidate: https://github.com/andymcca/lr-gpsp-nspire
- Preserve the existing working gpsp_libretro.tns; experimental outputs use separate names.
- Known working configuration: legacy old_video/video.c renderer, ROM buffer 8 MiB unchanged, Partial SMC, Full clean_dcache.
- Confirmed by user: original Emerald, Unbound, and Emerald Enhanced run; Wishes of Tomorrow v1.2.6 causes immediate white screen before logos and requires hard reset.
- Prior battle-transition crashes of Unbound/EE resolved by selecting the legacy video renderer.

## Run 001 goals
1. Pin and build upstream baseline without changing behavior.
2. Record toolchain version and reproducible build commands.
3. Add safe diagnostics and verify normal ROM behavior.
4. Investigate startup failure without assuming the ROM buffer is at fault.

Status: repository scaffolding only; no compiled emulator is available yet.
