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
     "Choose system clock or set custom date/time.\\n"
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
      "Store your clock in UltraGBA_Data and restart its\\n"
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

# Run004 layout verification: resolve parent folders from the actual executable
# path, never from a working directory changed by the document browser.
# Also make selected menu row inverse-video (currently near-invisible green).
paths = Path("upstream-gpsp/nspire_paths.c")
p = paths.read_text()
needle = 'char nspire_program_path[512];'
assert p.count(needle) == 1
p = p.replace(needle, needle + """
static char ugba_executable_dir[512];

/* Called during startup using the actual executable path (argv[0]).
   No fallback path should silently point to a parent directory. */
void ugba_set_executable_dir(const char *exe_path, const char *working_dir)
{
  char clean[512];
  const char *slash;
  nspire_normalize_path(clean, sizeof(clean), exe_path);
  slash = strrchr(clean, '/');
  if (slash) {
    if (slash == clean)
      snprintf(ugba_executable_dir, sizeof(ugba_executable_dir), "/");
    else
      snprintf(ugba_executable_dir, sizeof(ugba_executable_dir),
               "%.*s", (int)(slash - clean), clean);
  } else {
    /* A bare filename is resolved relative to the startup working dir. */
    snprintf(ugba_executable_dir, sizeof(ugba_executable_dir),
             "%s", working_dir);
  }
}
const char *ugba_get_executable_dir(void) { return ugba_executable_dir; }
""")
needle = '  snprintf(nspire_test_directory, sizeof(nspire_test_directory),\n           "%s/UltraGBA_Tests", emulator_dir);'
assert p.count(needle) == 1
p = p.replace(needle, '  snprintf(nspire_test_directory, sizeof(nspire_test_directory),\n           "%s/UltraGBA_Tests", ugba_get_executable_dir());')
# Save-file route must use same executor directory as test-folder route.
needle = '''  char program[512];
  const char *slash;
  nspire_normalize_path(program, sizeof(program), nspire_program_path);
  slash = strrchr(program, '/');
  if (slash)
    snprintf(out, size, "%.*s/UltraGBA_Data%s%s",
             (int)(slash - program), program, name[0] ? "/" : "", name);
  else
    snprintf(out, size, "UltraGBA_Data%s%s", name[0] ? "/" : "", name);'''
assert p.count(needle) == 1
p = p.replace(needle, '''  snprintf(out, size, "%s/UltraGBA_Data%s%s",
           ugba_get_executable_dir(), name[0] ? "/" : "", name);''')
paths.write_text(p)
hdr = Path("upstream-gpsp/nspire_paths.h")
h = hdr.read_text()
needle = 'void nspire_test_dir_init(const char *emulator_dir);'
assert h.count(needle) == 1
h = h.replace(needle, '''void ugba_set_executable_dir(const char *exe_path, const char *working_dir);
const char *ugba_get_executable_dir(void);
'''+needle)
hdr.write_text(h)
host = Path("upstream-gpsp/nspire_host_main.c")
h = host.read_text()
needle = '  nspire_test_dir_init(main_path);'
assert h.count(needle) == 1
h = h.replace(needle, '''  ugba_set_executable_dir(nspire_program_path, main_path);
  nspire_test_dir_init(ugba_get_executable_dir());''')
host.write_text(h)

gui = Path("upstream-gpsp/gui.c")
g = gui.read_text()
needle = '''        print_string_pad(line_buffer, COLOR_ACTIVE_ITEM, COLOR_BG, 10,
         (line * 10) + 40, 41);'''
assert g.count(needle) == 1
g = g.replace(needle, '''        /* Bright full-row inverse highlight for unmistakable selection. */
        print_string_pad(line_buffer, COLOR_BG, COLOR_ACTIVE_ITEM, 10,
         (line * 10) + 40, 41);''')
gui.write_text(g)
print("Run004: exe-relative Data/Tests layout and inverse selection highlight")

# Run005: persist a reference clock timestamp and compute elapsed time across
# emulator restarts. The user-entered time is an offset from the host time.
# If host time goes backwards, don't add negative elapsed time.
rtc = Path("upstream-gpsp/ultragba_custom_rtc.c")
code = rtc.read_text()
code = code.replace('''static int rtc_running;''','''static int rtc_running;
static time_t saved_host_time;
static time_t saved_game_time;''')
code = code.replace('''  rtc_epoch = mktime(&t);
  rtc_ticks = nspire_ticks();
  rtc_running = 1;''','''  rtc_epoch = mktime(&t);
  rtc_ticks = nspire_ticks();
  rtc_running = 1;
  saved_host_time = time(NULL);
  saved_game_time = rtc_epoch;''')
code = code.replace('''    fprintf(f, "%u %u %u %u %u %u\\n",
      (unsigned)ugba_rtc_mode, (unsigned)ugba_rtc_year,
      (unsigned)ugba_rtc_month, (unsigned)ugba_rtc_day,
      (unsigned)ugba_rtc_hour, (unsigned)ugba_rtc_minute);''','''    fprintf(f, "%u %u %u %u %u %u %lu %lu\\n",
      (unsigned)ugba_rtc_mode, (unsigned)ugba_rtc_year,
      (unsigned)ugba_rtc_month, (unsigned)ugba_rtc_day,
      (unsigned)ugba_rtc_hour, (unsigned)ugba_rtc_minute,
      (unsigned long)saved_host_time, (unsigned long)saved_game_time);''')
old = '''void ugba_rtc_load(void) {
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
}'''
new = '''void ugba_rtc_load(void) {
  char path[600];
  FILE *f;
  unsigned mode, year, month, day, hour, minute;
  unsigned long host_at_save = 0, game_at_save = 0;
  int count = 0;
  time_t host_now;
  struct tm t;
  rtc_filename(path, sizeof(path));
  f = fopen(path, "r");
  if (f) {
    count = fscanf(f, "%u %u %u %u %u %u %lu %lu",
               &mode, &year, &month, &day, &hour, &minute,
               &host_at_save, &game_at_save);
    fclose(f);
  }
  if (count >= 6) {
    ugba_rtc_mode = mode; ugba_rtc_year = year;
    ugba_rtc_month = month; ugba_rtc_day = day;
    ugba_rtc_hour = hour; ugba_rtc_minute = minute;
  }
  rtc_clamp();
  memset(&t, 0, sizeof(t));
  t.tm_year = 100 + (int)ugba_rtc_year;
  t.tm_mon = (int)ugba_rtc_month - 1;
  t.tm_mday = (int)ugba_rtc_day;
  t.tm_hour = (int)ugba_rtc_hour;
  t.tm_min = (int)ugba_rtc_minute;
  t.tm_isdst = -1;
  rtc_epoch = mktime(&t);
  host_now = time(NULL);
  /* A recorded host clock which keeps advancing across application restarts
     is useful even if its calendar date is wrong. Limit untrusted jumps. */
  if (count == 8 && host_at_save && host_now >= (time_t)host_at_save
      && host_now - (time_t)host_at_save < (time_t)366 * 86400) {
    rtc_epoch = (time_t)game_at_save + (host_now - (time_t)host_at_save);
  }
  saved_host_time = host_now;
  saved_game_time = rtc_epoch;
  rtc_ticks = nspire_ticks();
  rtc_running = 1;
  /* Old 6-field files still load, but cannot recover elapsed time until the
     user selects Apply and save RTC to upgrade the file format. */
}'''
assert old in code, "RTC load function shifted"
code = code.replace(old,new)
rtc.write_text(code)

gui = Path("upstream-gpsp/gui.c")
g = gui.read_text()
assert 'void submenu_custom_rtc() { ugba_rtc_apply(); }' in g
# The old code reset custom clock whenever the submenu was opened!
g = g.replace('void submenu_custom_rtc() { ugba_rtc_apply(); }',
              'void submenu_custom_rtc() { /* Do not reset clock on menu entry */ }')
gui.write_text(g)

host = Path("upstream-gpsp/nspire_host_main.c")
h = host.read_text()
needle = 'return len >= 5 && (!strncasecmp(value, "gpsp_", 5) || !strncasecmp(value, "_gpsp", 5));'
assert needle in h, "file associations detection changed"
h = h.replace(needle, '''return (len >= 5 && (!strncasecmp(value, "gpsp_", 5) ||
                               !strncasecmp(value, "_gpsp", 5))) ||
         (len >= 8 && !strncasecmp(value, "UltraGBA", 8));''')
host.write_text(h)
print("Run005: RTC host reference persistence, no submenu reset, rebinding of prior UltraGBA associations")

# Run006: The user's ndless.cfg.tns has only image-viewer associations.
# register_rom_types previously handled obsolete gpSP values but did NOT
# append ext.gba/ext.gbz when the keys were missing. Fix append-only behavior.
host = Path("upstream-gpsp/nspire_host_main.c")
h = host.read_text()
needle = 'static void register_rom_types(const char *exe_path)\n{'
assert h.count(needle) == 1
helper = r"""
/* Add missing ROM file associations without modifying any existing
   non-UltraGBA association. ndless.cfg.tns may exist but omit both keys.
   Read-only scan followed by append; leave existing image viewer keys intact.
   Result is visible the next time the OS/Ndless reloads its associations. */
static void ugba_add_missing_rom_types(const char *name)
{
  const char *docs = get_documents_dir();
  size_t dlen = strlen(docs);
  char path[600];
  char line[512];
  unsigned seen[NUM_ROM_TYPES] = {0};
  FILE *f;
  unsigned i;
  int last_char = '\n';

  snprintf(path, sizeof(path), "%s%sndless/ndless.cfg.tns",
           docs, (dlen && docs[dlen - 1] == '/') ? "" : "/");
  f = fopen(path, "rb");
  if (!f)
    return;  /* Don't create an Ndless configuration outside its own setup. */
  while (fgets(line, sizeof(line), f)) {
    size_t n = strlen(line);
    if (n) last_char = (unsigned char)line[n - 1];
    for (i = 0; i < NUM_ROM_TYPES; i++) {
      char key[16];
      snprintf(key, sizeof(key), "ext.%s=", rom_types[i]);
      if (!strncmp(line, key, strlen(key))) seen[i] = 1;
    }
  }
  if (ferror(f)) { fclose(f); return; }
  fclose(f);

  if (seen[0] && seen[1])
    return;
  f = fopen(path, "ab");
  if (!f) return;
  if (last_char != '\n' && last_char != '\r')
    fputc('\n', f);
  for (i = 0; i < NUM_ROM_TYPES; i++) {
    if (!seen[i])
      fprintf(f, "ext.%s=%s\n", rom_types[i], name);
  }
  fclose(f);
}
"""
h = h.replace(needle, helper + '\n' + needle)
needle = '''  for (i = 0; i < NUM_ROM_TYPES; i++)
    cfg_register_fileext(rom_types[i], name);'''
assert h.count(needle) == 1
h = h.replace(needle, needle + '\n  ugba_add_missing_rom_types(name);')
host.write_text(h)
print("Run006: append missing ext.gba/ext.gbz without touching existing mappings")

# Run007: Stop all Ndless configuration mutation. The calculator owner reports
# Run006 cfg writes do not affect launching from the native Documents browser.
# Retain support for argv[1] ROM launches, but make registration opt-in/manual.
host = Path("upstream-gpsp/nspire_host_main.c")
h = host.read_text()
start = h.index('static const char *const rom_types[] = { "gba", "gbz" };')
end = h.index('int main(int argc, char *argv[])', start)
section = h[start:end]
assert 'retarget_rom_types' in section
assert 'ugba_add_missing_rom_types' in section
assert 'register_rom_types' in section
h = h[:start] + h[end:]
assert h.count('  register_rom_types(argv[0]);') == 1
h = h.replace('  register_rom_types(argv[0]);', '  /* Run007: do not alter Ndless file associations on launch. */')
host.write_text(h)
print("Run007: removed all ndless.cfg.tns writes/registration; argv ROM support retained")
