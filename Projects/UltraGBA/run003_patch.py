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
new_migration = '''/* Never relocate or erase original saves: import only when no target exists.
 * The legacy central directory remains intact for rollback to older gpSP. */
static void copy_legacy_save(const char *old_path, const char *new_path)
{
  FILE *src, *dst;
  unsigned char chunk[8192];
  size_t n;
  int ok = 1;
  struct stat st;
  if (!strcmp(old_path, new_path) || stat(new_path, &st) == 0)
    return;
  src = fopen(old_path, "rb");
  if (!src)
    return;
  dst = fopen(new_path, "wb");
  if (!dst) {
    fclose(src);
    return;
  }
  while ((n = fread(chunk, 1, sizeof(chunk), src)) != 0)
    if (fwrite(chunk, 1, n, dst) != n) {
      ok = 0;
      break;
    }
  if (ferror(src))
    ok = 0;
  if (fclose(dst) != 0)
    ok = 0;
  fclose(src);
  if (!ok)
    remove(new_path);
}

void nspire_game_move_old_files(const char *rom_path)
{
  char name[300], old_base[512], new_base[512], old_path[600], new_path[600];
  static const char *const extensions[] =
      { ".sav.tns", ".sav.gz.tns", ".settings.tns" };
  unsigned i, slot;
  nspire_game_name(rom_path, name, sizeof(name));
  nspire_save_file(old_base, sizeof(old_base), name);
  nspire_game_base(rom_path, new_base, sizeof(new_base));
  for (i = 0; i < sizeof(extensions) / sizeof(extensions[0]); i++) {
    snprintf(old_path, sizeof(old_path), "%s%s", old_base, extensions[i]);
    snprintf(new_path, sizeof(new_path), "%s%s", new_base, extensions[i]);
    copy_legacy_save(old_path, new_path);
  }
  for (slot = 0; slot < STATE_SLOTS; slot++) {
    snprintf(old_path, sizeof(old_path), "%s%u.svs.tns", old_base, slot);
    snprintf(new_path, sizeof(new_path), "%s%u.svs.tns", new_base, slot);
    copy_legacy_save(old_path, new_path);
  }
}
'''
s = s[:start] + new_migration + s[end:]
source.write_text(s)
print("Patched save paths and non-destructive legacy import in nspire_states.c")
