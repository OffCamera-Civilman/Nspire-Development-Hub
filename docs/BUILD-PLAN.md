# Nspire Development Hub Build Plan

## Target
TI-Nspire CX II CAS, OS 6.2.0.333; Ndless executable outputs (.tns). GitHub Actions should run on an Ubuntu runner with a reproducible Ndless toolchain/container.

## Milestones
1. Verify upstream gpSP fork, chosen version, license, and documented build instructions.
2. Add build script and workflow that builds a known-good **unmodified** executable.
3. Archive binary as an Actions artifact named with the run number.
4. Test on hardware with already-working ROMs before testing problematic ROMs.
5. Iterate on logs, crash diagnostics, and compatibility.

## Safety
- Never replace the user's existing gpsp_libretro.tns during testing.
- No known-crashing game should be retried until a diagnostic or change justifies it.
- ROMs, BIOS files, and user saves should not be committed to this public repository.
