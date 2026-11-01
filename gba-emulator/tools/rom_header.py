#!/usr/bin/env python3
"""Inspect a local GBA ROM header without modifying or uploading the ROM."""
import argparse
import hashlib
import json
from pathlib import Path

def inspect(path):
    path = Path(path)
    with path.open("rb") as stream:
        header = stream.read(0xC0)
    if len(header) < 0xC0:
        raise ValueError("File too small for a GBA header")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    checksum = (-(sum(header[0xA0:0xBD]) + 0x19)) & 0xff
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "title": header[0xA0:0xAC].rstrip(b"\0 ").decode("ascii", "replace"),
        "game_code": header[0xAC:0xB0].decode("ascii", "replace"),
        "checksum_valid": checksum == header[0xBD],
        "sha256": digest.hexdigest(),
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom")
    print(json.dumps(inspect(parser.parse_args().rom), indent=2))
