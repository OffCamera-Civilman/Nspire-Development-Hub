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
# Keep ALL emulator-managed files alongside the emulator in UltraGBA_Data.
# Do not move or delete anything in old /documents/zgpSP_saves.
paths = Path("upstream-gpsp/nspire_paths.c")
p = paths.read_text()
old = '''void nspire_save_file(char *out, size_t size, const char *name)
{
  const char *docs = get_documents_dir();
  size_t len = strlen(docs);

  snprintf(out, size, "%s%s%s%s%s", docs, len && docs[len - 1] == '/' ? "" : "/", SAVE_FOLDER,
           name[0] ? "/" : "", name);
}
'''
new = '''void nspire_save_file(char *out, size_t size, const char *name)
{
  char program[512];
  const char *slash;
  nspire_normalize_path(program, sizeof(program), nspire_program_path);
  slash = strrchr(program, '/');
  if (slash)
    snprintf(out, size, "%.*s/UltraGBA_Data%s%s",
             (int)(slash - program), program, name[0] ? "/" : "", name);
  else
    snprintf(out, size, "UltraGBA_Data%s%s", name[0] ? "/" : "", name);
}
'''
assert p.count(old) == 1, "nspire_save_file layout changed"
p = p.replace(old, new)
paths.write_text(p)

host = Path("upstream-gpsp/nspire_host_main.c")
code = host.read_text()
needle = '''  nspire_move_old_documents_files();
  nspire_move_old_files(main_path, 1);
'''
assert code.count(needle) == 1, "legacy auto-migration layout changed"
code = code.replace(needle, '''  /* Run004: keep existing old saves and settings untouched; never auto-migrate. */
''')
host.write_text(code)
print("Run004: ROM-local saves, UltraGBA_Tests and emulator-local UltraGBA_Data; no migration")


# Custom RTC: date/time entered through Emulator options -> Custom RTC.
# A persistent emulator-local file stores entered clock. It advances using
# the independent 32768Hz timer while running. No nClock hook modifications.
rtc_header = """#ifndef ULTRAGBA_CUSTOM_RTC_H
#define ULTRAGBA_CUSTOM_RTC_H
#include <time.h>
#include "common.h"
extern u32 ugba_rtc_mode, ugba_rtc_year, ugba_rtc_month, ugba_rtc_day;
extern u32 ugba_rtc_hour, ugba_rtc_minute;
void ugba_rtc_load(void);
void ugba_rtc_apply(void);
void ugba_rtc_get(struct tm *result);
#endif
"""
Path("upstream-gpsp/ultragba_custom_rtc.h").write_text(rtc_header)
rtc_source = r"""#include "ultragba_custom_rtc.h"
#include "nspire_paths.h"
#include "nspire.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* RTC mode changes only the time source, NOT cartridge RTC detection. */
u32 ugba_rtc_mode = 0;      /* 0 system / 1 custom */
u32 ugba_rtc_year = 26;     /* 2000+ */
u32 ugba_rtc_month = 11;
u32 ugba_rtc_day = 8;
u32 ugba_rtc_hour = 12;
u32 ugba_rtc_minute = 0;
static time_t rtc_epoch;
static u32 rtc_ticks;
static int rtc_running;

static void rtc_filename(char *path, size_t size) {
  nspire_save_file(path, size, "custom_rtc.txt.tns");
}
static void rtc_clamp(void) {
  if (ugba_rtc_year > 99) ugba_rtc_year = 26;
  if (ugba_rtc_month < 1 || ugba_rtc_month > 12) ugba_rtc_month = 1;
  if (ugba_rtc_day < 1 || ugba_rtc_day > 31) ugba_rtc_day = 1;
  if (ugba_rtc_hour > 23) ugba_rtc_hour = 0;
  if (ugba_rtc_minute > 59) ugba_rtc_minute = 0;
  ugba_rtc_mode %= 2;
}
void ugba_rtc_apply(void) {
  struct tm t;
  char path[600];
  FILE *f;
  rtc_clamp();
  memset(&t, 0, sizeof(t));
  t.tm_year = 100 + (int)ugba_rtc_year;
  t.tm_mon = (int)ugba_rtc_month - 1;
  t.tm_mday = (int)ugba_rtc_day;
  t.tm_hour = (int)ugba_rtc_hour;
  t.tm_min = (int)ugba_rtc_minute;
  t.tm_isdst = -1;
  rtc_epoch = mktime(&t);
  rtc_ticks = nspire_ticks();
  rtc_running = 1;
  rtc_filename(path, sizeof(path));
  f = fopen(path, "w");
  if (f) {
    fprintf(f, "%u %u %u %u %u %u\n",
      (unsigned)ugba_rtc_mode, (unsigned)ugba_rtc_year,
      (unsigned)ugba_rtc_month, (unsigned)ugba_rtc_day,
      (unsigned)ugba_rtc_hour, (unsigned)ugba_rtc_minute);
    fclose(f);
  }
}
void ugba_rtc_load(void) {
  char path[600];
  FILE *f;
  unsigned mode, year, month, day, hour, minute;
  rtc_filename(path, sizeof(path));
  f = fopen(path, "r");
  if (f) {
    if (fscanf(f, "%u %u %u %u %u %u",
               &mode, &year, &month, &day, &hour, &minute) == 6) {
      ugba_rtc_mode = mode; ugba_rtc_year = year;
      ugba_rtc_month = month; ugba_rtc_day = day;
      ugba_rtc_hour = hour; ugba_rtc_minute = minute;
    }
    fclose(f);
  }
  ugba_rtc_apply();
}
void ugba_rtc_get(struct tm *result) {
  time_t now;
  struct tm *t;
  if (ugba_rtc_mode && rtc_running) {
    /* unsigned subtraction handles wrap; timer is ~36h per turn. */
    now = rtc_epoch + (time_t)((u32)(nspire_ticks() - rtc_ticks) / 32768u);
  } else {
    time(&now);
  }
  t = localtime(&now);
  if (t) *result = *t;
  else memset(result, 0, sizeof(*result));
}
"""
Path("upstream-gpsp/ultragba_custom_rtc.c").write_text(rtc_source)
makefile = Path("upstream-gpsp/Makefile")
m = makefile.read_text()
assert m.count("nspire_config.o nspire_clock.o") == 1
m = m.replace("nspire_config.o nspire_clock.o",
              "nspire_config.o ultragba_custom_rtc.o nspire_clock.o")
makefile.write_text(m)

gba = Path("upstream-gpsp/libretro-gpsp/gba_memory.c")
g = gba.read_text()
needle = '#include "../nspire_gbz.h"'
assert g.count(needle) == 1
g = g.replace(needle, needle + '\n#include "../ultragba_custom_rtc.h"')
needle = '''time(&current_time_flat);
            current_time = localtime(&current_time_flat);'''
assert g.count(needle) == 2, "RTC command handler changed"
g = g.replace(needle, '''{
              static struct tm rtc_snapshot;
              ugba_rtc_get(&rtc_snapshot);
              current_time = &rtc_snapshot;
            }''')
gba.write_text(g)

host = Path("upstream-gpsp/nspire_host_main.c")
h = host.read_text()
needle = '#include "nspire_clock.h"'
assert h.count(needle) == 1
h = h.replace(needle, needle + '\n#include "ultragba_custom_rtc.h"')
needle = '  nspire_test_dir_init(main_path);'
assert h.count(needle) == 1
h = h.replace(needle, needle + '\n  ugba_rtc_load();')
host.write_text(h)

gui = Path("upstream-gpsp/gui.c")
g = gui.read_text()
needle = '#if defined(NSPIRE_LIBRETRO)\n  u8 *bios_source_options[]'
assert g.count(needle) == 1
g = g.replace(needle, '''#if defined(NSPIRE_LIBRETRO)
  u8 *ugba_rtc_mode_options[] = { "system", "custom" };
  u8 *bios_source_options[]''')
needle = '    string_selection_option(NULL, "Interframe blending", nspire_frame_mix_options,'
assert g.count(needle) == 1
g = g.replace(needle, '''    submenu_option(&custom_rtc_menu, "Custom RTC",
     "Choose system clock or set custom date/time.\n"
     "Use Apply and save before leaving.", 6),
'''+needle)
# Add submenu before emulator menu option declaration.
needle = '  menu_option_type emulator_options[] ='
assert g.count(needle) == 1
g = g.replace(needle, '''  void submenu_custom_rtc() { ugba_rtc_apply(); }
  menu_option_type custom_rtc_options[] = {
    string_selection_option(NULL, "Clock source", ugba_rtc_mode_options,
      &ugba_rtc_mode, 2, "System or manually-set custom clock.", 0),
    numeric_selection_option(NULL, "Year (2000+)", &ugba_rtc_year, 100,
      "26 means 2026. Use left/right to change.", 1),
    numeric_selection_option(NULL, "Month", &ugba_rtc_month, 13,
      "1-12; value 0 is clamped to 1 on Apply.", 2),
    numeric_selection_option(NULL, "Day", &ugba_rtc_day, 32,
      "1-31; invalid calendar dates normalize.", 3),
    numeric_selection_option(NULL, "Hour (24h)", &ugba_rtc_hour, 24,
      "0-23.", 4),
    numeric_selection_option(NULL, "Minute", &ugba_rtc_minute, 60,
      "0-59.", 5),
    action_option(ugba_rtc_apply, NULL, "Apply and save RTC",
      "Store your clock in UltraGBA_Data and restart its\n"
      "timer from the entered date and time.", 7),
    submenu_option(NULL, "Back", "Return to emulator options.", 9)
  };
  make_menu(custom_rtc, submenu_custom_rtc, NULL);

'''+needle)
# include only once near existing headers
needle = '#include "nspire_config.h"'
if needle not in g:
  needle = '#include "nspire_clock.h"'
assert g.count(needle) >= 1, "RTC GUI include point not found"
g = g.replace(needle, needle + '\n#include "ultragba_custom_rtc.h"', 1)
gui.write_text(g)
print("Run004 custom RTC menu, persistent clock, and GBA RTC bridge patched")
