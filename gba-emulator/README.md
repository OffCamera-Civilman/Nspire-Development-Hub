# GBA emulator project

This directory tracks investigation and development of a GBA emulator for the TI-Nspire CX II CAS.

## Stages

**Stage 1: Reproduce and instrument**
- Record emulator binary/version, launch path, video configuration, and ROM metadata.
- Separate immediate boot white screen from first-battle crash.
- Find a reliable way to log launch milestones before touching rendering.
- Verify the same emulator can still run known-good games.

**Stage 2: Analyze existing emulator**
- Identify the exact upstream source and license for the installed gpSP/libretro port.
- Map ROM loading, memory allocation, ARM CPU execution, BIOS handling and GPU frame presentation.
- Test hypotheses one at a time: memory mapping, unsupported ROM access, save initialization, renderer, and timing.

**Stage 3: Implement**
- Build a small, reproducible Ndless toolchain.
- Make minimal compatibility fixes in a source-available emulator before attempting a rewrite.
- Add smoke tests and regression cases.
- Produce a `.tns` only after a build can actually be verified.

## Important constraints

A game running on another emulator does not establish that it will run on the TI-Nspire. ROM file size alone does not explain an immediate white screen; the root cause is **not determined**.

Do not distribute copyrighted BIOS or commercial ROM images in this repository.
