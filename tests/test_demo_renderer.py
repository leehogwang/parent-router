from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_demo.py"
SPEC = importlib.util.spec_from_file_location("demo_builder", MODULE_PATH)
demo = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = demo
SPEC.loader.exec_module(demo)


class DemoRendererTests(unittest.TestCase):
    def test_strip_script_bookends(self) -> None:
        payload = (
            b"Script started on 2026-04-10 00:00:00+09:00 [COMMAND=\"claude\"]\n"
            b"\x1b[31mhello\x1b[0m\r\n"
            b"\nScript done on 2026-04-10 00:00:01+09:00 [COMMAND_EXIT_CODE=\"0\"]\n"
        )
        self.assertEqual(demo.strip_script_bookends(payload), b"\x1b[31mhello\x1b[0m\r\n")

    def test_parse_timing_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "timing.log"
            path.write_text(
                "\n".join(
                    [
                        "H 0.000000 START_TIME 2026-04-10 00:00:00+09:00",
                        "O 0.050000 7",
                        "I 0.010000 3",
                    ]
                ),
                encoding="utf-8",
            )
            entries = demo.parse_timing_entries(path)
        self.assertEqual([(entry.stream, entry.size) for entry in entries], [("O", 7), ("I", 3)])

    def test_compress_delay(self) -> None:
        self.assertEqual(demo.compress_delay(0), 0.0)
        self.assertEqual(demo.compress_delay(0.01), demo.MIN_EVENT_SECONDS)
        self.assertEqual(demo.compress_delay(5.0), demo.MAX_HOLD_SECONDS)

    def test_clean_terminal_output(self) -> None:
        data = (
            b"Script started on 2026-04-10 00:00:00+09:00 [COMMAND=\"claude\"]\n"
            b"\x1b[?1049h\x1b[H/parent --dry-run rename one variable\r\n"
            b"\x1b[34mChosen route: haiku\x1b[0m\r\n"
            b"\nScript done on 2026-04-10 00:00:01+09:00 [COMMAND_EXIT_CODE=\"0\"]\n"
        )
        cleaned = demo.clean_terminal_output(data)
        self.assertIn("/parent --dry-run rename one variable", cleaned)
        self.assertIn("Chosen route: haiku", cleaned)
        self.assertNotIn("\x1b", cleaned)


if __name__ == "__main__":
    unittest.main()
