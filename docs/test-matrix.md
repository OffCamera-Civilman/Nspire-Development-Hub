# Emulator test matrix

| Test | Observed behavior | Next diagnostic |
| --- | --- | --- |
| Pokémon Wishes of Tomorrow | White screen immediately after selecting ROM; hard reset needed | Add milestones for file open, ROM load, CPU reset, first frame |
| Pokémon Unbound | Has run with existing settings | Preserve working configuration and capture version |
| Enhanced Emerald | Has run with existing settings | Preserve working configuration and capture version |
| Other ROM (not yet identified) | Game loads; crash at first wild battle | Capture first battle transition, save and graphics states |

## Device configuration

- TI-Nspire CX II CAS, OS 6.2.0.333
- Previously successful settings should be recorded exactly before changing them.
- User reported they did not change the ROM buffer.

## Test record template

- Date:
- Emulator executable SHA-256:
- Emulator build/source:
- Ndless version:
- ROM filename/version (no ROM upload):
- ROM file SHA-256:
- Configuration:
- Last visible screen:
- Time to failure:
- Hard reset needed:
- Repeatable (number of trials):
