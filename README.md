# Nspire Development Hub

Development workspace for the **TI-Nspire CX II CAS** running OS **6.2.0.333**, with Ndless-based programs and builds.

## Project areas

- [GBA emulator investigation](gba-emulator/README.md) — compatibility, rendering, and crash analysis.
- [Emulator test matrix](docs/test-matrix.md) — reproducible regression cases.
- Future work: Python IDE, utilities, and automated builds.

## Current status

Initial project structure and testing documentation are in place. **No replacement GBA emulator has been built or tested yet.**

### Emulator development priorities

1. Identify the exact source/version of the installed gpSP/libretro emulator.
2. Investigate immediate white-screen failures (Wishes of Tomorrow).
3. Investigate separate first-wild-battle crashes.
4. Maintain compatibility with previously working Unbound and Enhanced Emerald configurations.
5. Build and test an Ndless-compatible `.tns` after source/toolchain validation.

### Contributing

Report the ROM version, checksum, tested emulator build, configuration, and exact failure stage in an issue. Please do not upload copyrighted ROMs, BIOS files, or commercial game assets.
