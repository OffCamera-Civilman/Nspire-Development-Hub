import tempfile
import unittest
from pathlib import Path
from rom_header import inspect

class HeaderTests(unittest.TestCase):
    def test_synthetic_rom(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "test.gba"
            h = bytearray(0xC0)
            h[0xA0:0xAC] = b"TESTGAME    "
            h[0xAC:0xB0] = b"TEST"
            h[0xBD] = (-(sum(h[0xA0:0xBD]) + 0x19)) & 0xff
            p.write_bytes(h)
            result = inspect(p)
            self.assertTrue(result["checksum_valid"])
            self.assertEqual(result["game_code"], "TEST")
            self.assertEqual(result["bytes"], 192)

if __name__ == "__main__":
    unittest.main()
