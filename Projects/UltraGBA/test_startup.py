"""Exercise a game launch, a missing ROM and side-by-side saves on the host frontend."""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_frontend(executable, game_folder, output, script, *games):
    commands = output / "keys.txt"
    commands.write_text(script)
    subprocess.run(
        [str(executable), str(commands), str(output), str(game_folder), *games],
        check=True,
        timeout=140,
    )


def check_startup(executable, pattern, documents):
    games = documents / "gba"
    games.mkdir()
    output = documents / "captures"
    output.mkdir()
    shutil.copyfile(pattern, games / "Pattern.gba.tns")
    (games / "_gpSP.tns").write_bytes(b"host test executable")
    originals = {
        "ndless/ndless.cfg.tns": b"ext.gba=gpsp_original\next.gbz=gpsp_original\n",
        "gpSP_saves/Existing.gba.sav.tns": b"older save",
        "zgpSP_saves/Pattern.gba.sav.tns": b"current save",
        "gba/Pattern.gba.sav.tns": b"save alongside ROM",
        "gba/Pattern.gba0.svs.tns": b"existing state",
        "gba/gpsp.cfg.tns": bytes(148),
    }
    for name, data in originals.items():
        path = documents / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)

    run_frontend(executable, games, output, """wait 1
press enter
wait 2
note early
wait 1
note late
press Q
wait 1
quit
""")
    report = (output / "report.txt").read_text()
    frames = re.findall(r"^note (early|late) .*?\bframe=(\d+)\b.*?game=Pattern\.gba\.tns$", report, re.M)
    assert [name for name, _ in frames] == ["early", "late"], report
    assert 0 < int(frames[0][1]) < int(frames[1][1]), frames
    saves = documents / "UltraGBA_Test"
    trace = saves / "boot.txt.tns"
    lines = trace.read_text().splitlines()
    assert lines[1].startswith("Selected: ") and lines[1].endswith("/Pattern.gba.tns"), lines
    assert lines[2:] == [
        f"File bytes: {pattern.stat().st_size}",
        "Reading ROM: cache=8 MiB renderer=1 smc=0 full_clean=1",
        "ROM loaded; starting GBA reset",
        "GBA reset complete",
        "Game ready for execution",
        "First frame presented",
    ], lines
    assert (saves / "Pattern.gba0.svs.tns").stat().st_size > 0
    print(f"Pattern ran from frame {frames[0][1]} to {frames[1][1]} and saved a new state.")

    run_frontend(executable, games, output, "wait 2\nquit\n", "Missing.gba.tns")
    lines = trace.read_text().splitlines()
    assert lines[1].endswith("/Missing.gba.tns") and lines[-1].startswith("ROM load failed:"), lines
    assert "First frame presented" not in lines
    for name, expected in originals.items():
        assert (documents / name).read_bytes() == expected, name
    print("Missing-ROM trace, legacy saves and Ndless file associations verified.")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        check_startup(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(tmp))
