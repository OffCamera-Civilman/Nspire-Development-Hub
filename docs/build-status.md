# Build status

## Run001: Ndless smoke app

A minimal C program and an experimental GitHub Actions workflow were added.

- Source: `tools/ndless-smoke/main.c`
- Makefile: `tools/ndless-smoke/Makefile`
- Workflow: `.github/workflows/ndless-smoke-build.yml`
- Expected artifact if CI passes: `NspireSmoke_Run001.tns`

**Validation pending:** The historical `ndless/ndless-sdk` container may lack current GitHub Actions dependencies or may differ from current upstream Ndless. A successful GitHub Actions job and device test are required before describing this as a confirmed working calculator build.

Do not install a smoke-test build if GitHub reports an unsuccessful workflow. This is a toolchain plumbing test, **not** the emulator.
