from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "parent_stats.py"
SPEC = importlib.util.spec_from_file_location("parent_stats", MODULE_PATH)
parent_stats = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = parent_stats
SPEC.loader.exec_module(parent_stats)


class ParentStatsTests(unittest.TestCase):
    def test_load_stats_args_prefers_stdin(self) -> None:
        with mock.patch.object(
            sys, "stdin", io.StringIO("--limit 5 --date 2026-04-10")
        ):
            args = parent_stats.load_stats_args(["parent_stats.py", "--limit", "2"])
        self.assertEqual(args.limit, 5)
        self.assertEqual(args.date, "2026-04-10")

    def test_parse_raw_args_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--limit 0")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--date 2026/04/10")

    def test_load_run_records_and_format_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            records = [
                {
                    "timestamp": "2026-04-10T10:00:00+00:00",
                    "profile": "parent",
                    "selected_model": "opus",
                    "selected_mode": "plan",
                    "confidence": "high",
                    "execution_status": "ok",
                    "request_text": "Plan a migration for auth",
                },
                {
                    "timestamp": "2026-04-10T09:00:00+00:00",
                    "profile": "parent-no-opus",
                    "selected_model": "sonnet",
                    "selected_mode": "execute",
                    "confidence": "medium",
                    "execution_status": None,
                    "request_text": "Rename one variable safely",
                },
            ]
            for index, record in enumerate(records):
                (run_dir / f"20260410T0{index}0000Z-parent.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )

            args = parent_stats.StatsArgs(limit=2, date="2026-04-10")
            paths = parent_stats.iter_run_json_files(root, args)
            loaded = parent_stats.load_run_records(paths, args.limit)
            report = parent_stats.format_report(loaded, args)

        self.assertEqual(len(loaded), 2)
        self.assertIn("Runs analyzed: 2", report)
        self.assertIn("Status: dry-run=1, ok=1", report)
        self.assertIn("Profiles: parent=1, parent-no-opus=1", report)
        self.assertIn("Models: opus=1, sonnet=1", report)
        self.assertIn("Recent runs:", report)
        self.assertIn("Plan a migration for auth", report)

    def test_main_reports_no_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                parent_stats.os.environ,
                {"PARENTS_PROJECT_ROOT": tmpdir},
                clear=False,
            ):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    exit_code = parent_stats.main(
                        ["parent_stats.py", "--date", "2026-04-10"]
                    )
        self.assertEqual(exit_code, 0)
        self.assertIn("No run logs found.", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
