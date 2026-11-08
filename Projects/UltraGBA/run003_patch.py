#!/usr/bin/env python3
"""Run003 patch: per-ROM save paths and emulator-adjacent test logs.

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
# Put all generated test logs in UltraGBA_Tests beside emulator, not beside ROMs.
header = Path("upstream-gpsp/nspire_paths.h")
h = header.read_text()
needle = 'void nspire_save_file(char *out, size_t size, const char *name);'
assert h.count(needle) == 1
h = h.replace(needle, needle + """
/* Test reports only: <emulator-folder>/UltraGBA_Tests/<name>. */
void nspire_test_dir_init(const char *emulator_dir);
void nspire_test_file(char *out, size_t size, const char *name);
""")
header.write_text(h)

paths = Path("upstream-gpsp/nspire_paths.c")
p = paths.read_text()
needle = 'char nspire_program_path[512];'
assert p.count(needle) == 1
p = p.replace(needle, needle + """
static char nspire_test_directory[600];

void nspire_test_dir_init(const char *emulator_dir)
{
  struct stat st;
  snprintf(nspire_test_directory, sizeof(nspire_test_directory),
           "%s/UltraGBA_Tests", emulator_dir);
  if (stat(nspire_test_directory, &st) != 0)
    mkdir(nspire_test_directory, 0755);
}

void nspire_test_file(char *out, size_t size, const char *name)
{
  if (nspire_test_directory[0])
    snprintf(out, size, "%s/%s", nspire_test_directory, name);
  else
    nspire_save_file(out, size, name);
}
""")
paths.write_text(p)

host = Path("upstream-gpsp/nspire_host_main.c")
code = host.read_text()
needle = '  snprintf(nspire_program_path, sizeof(nspire_program_path), "%s", argv[0]);'
assert code.count(needle) == 1
code = code.replace(needle, needle + '\n  nspire_test_dir_init(main_path);')
needle = 'nspire_save_file(path, sizeof(path), "gpsp_results.txt.tns");'
assert code.count(needle) == 1
code = code.replace(needle, 'nspire_test_file(path, sizeof(path), "gpsp_results.txt.tns");')
host.write_text(code)

frames = Path("upstream-gpsp/nspire_frameskip.c")
code = frames.read_text()
needle = 'nspire_save_file(path, sizeof(path), "gpsp_perf.txt.tns");'
assert code.count(needle) == 1
code = code.replace(needle, 'nspire_test_file(path, sizeof(path), "gpsp_perf.txt.tns");')
frames.write_text(code)
print("Patched ROM-local saves, SDK timestamps and emulator-adjacent UltraGBA_Tests outputs")
