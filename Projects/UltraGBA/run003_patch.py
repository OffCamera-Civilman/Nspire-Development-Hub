#!/usr/bin/env python3
"""Run003 patch: per-ROM save paths with non-destructive legacy save import.

Applies to pinned upstream gpSP source in CI. Refuses to patch unknown layout.
"""
from pathlib import Path

source = Path("upstream-gpsp/nspire_states.c")
s = source.read_text()
old_base = '''void nspire_game_base(const char *rom_path, char *out, size_t size)
{
  char name[300];
  nspire_game_name(rom_path, name, sizeof(name));
  nspire_save_file(out, size, name);
}
'''
new_base = '''void nspire_game_base(const char *rom_path, char *out, size_t size)
{
  char name[300], normalized[512];
  const char *slash;
  size_t n;
  nspire_game_name(rom_path, name, sizeof(name));
  nspire_normalize_path(normalized, sizeof(normalized), rom_path);
  slash = strrchr(normalized, '/');
  n = slash ? (size_t)(slash - normalized) + 1 : 0;
  snprintf(out, size, "%.*s%s", (int)n, normalized, name);
}
'''
assert s.count(old_base) == 1, "nspire_game_base layout has changed"
s = s.replace(old_base, new_base)
start = s.index("void nspire_game_move_old_files(const char *rom_path)\n{")
end = s.index("\nvoid states_file_name(", start)
new_migration = '''/* New saves stay beside the selected ROM. Legacy central saves are not moved. */
void nspire_game_move_old_files(const char *rom_path)
{
  (void)rom_path;
}
'''
s = s[:start] + new_migration + s[end:]
source.write_text(s)
# Older SDK exposes st_mtime rather than st_mtim; use compatible seconds field.
for name in ("nspire_states.c", "nspire_backup.c"):
    file = Path("upstream-gpsp") / name
    code = file.read_text()
    code = code.replace("st.st_mtim.tv_sec", "st.st_mtime")
    file.write_text(code)
print("Patched ROM-local saves (no migration) and SDK timestamps")
