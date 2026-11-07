# UltraGBA Run001

An experimental Game Boy Advance emulator for the TI-Nspire CX II CAS running Ndless. The Run001 target is OS 6.4.0.74. The earlier NspireSmoke Run001 executable passed its launch test on this device. This emulator has its own hardware test.

## Try it on the calculator

1. Put `UltraGBA_Run001.tns` and the included `UltraGBA_Pattern_Run001.gba.tns` in the same calculator folder, for example `/test/`.
2. Launch the emulator from Documents. Select the pattern cartridge in its file browser and press Enter. Look for a moving stripe on a colored background. Q saves and quits with the default keys.
3. Open the emulator again and browse to a known-working game such as Pokémon Unbound. Then try Wishes of Tomorrow. Use your own ROMs.
4. After a white screen, retrieve `/UltraGBA_Test/boot.txt.tns` before opening another game in UltraGBA. The log records the most recently selected game, file size when available, ROM load, CPU reset and first frame submitted for display. A completed first frame can still be a white frame.

## Test profile

UltraGBA stores its saves, states, settings and startup log in `/UltraGBA_Test/`. It skips the upstream automatic save migration and ROM association registration. Open this executable directly to use it. New profiles start with the legacy video renderer, 8 MiB ROM cache, Partial SMC and Full clean_dcache. The emulator retains its own later settings. An open-source GBA BIOS is compiled into the emulator.

## Build and verify

The build uses the standalone [lr-gpSP Nspire source at 2ddeb23](https://github.com/andymcca/lr-gpsp-nspire/tree/2ddeb23b565cab84e20278bb73ed76f3d91b25f5), the upstream test cartridge and the local `run001.patch`. The patch isolates the test profile and adds a startup log. The emulation core comes from the pinned source.

With the Ndless SDK, Git, make, GCC/G++, Python 3 and the host zlib development package installed, run `bash Projects/UltraGBA/build.sh /tmp/ultragba-dist` from the hub. The script checks the ARM build, launches the pattern cartridge on the upstream host simulator, checks an independent save state and a missing-ROM log, and verifies the original saves and ROM associations. CI records the installed SDK and compiler versions and the SHA-256 of each calculator file. The source artifact contains the patched tree and the upstream license in `libretro-gpsp/COPYING`.

Physical compatibility with Wishes of Tomorrow remains to be tested.
