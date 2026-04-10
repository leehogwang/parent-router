from __future__ import annotations

import datetime
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
            sys,
            "stdin",
            io.StringIO(
                "--limit 5 --date 2026-04-10 --since 2026-04-09 --until 2026-04-10 --window 7d --status ok --profile parent --mode plan --model opus --confidence high --format json --reasons-only --fail-if-empty --summary-only --show-paths --sort oldest"
            ),
        ):
            args = parent_stats.load_stats_args(["parent_stats.py", "--limit", "2"])
        self.assertEqual(args.limit, 5)
        self.assertEqual(args.date, "2026-04-10")
        self.assertEqual(args.since, "2026-04-09")
        self.assertEqual(args.until, "2026-04-10")
        self.assertEqual(args.window, "7d")
        self.assertEqual(args.status, "ok")
        self.assertEqual(args.profile, "parent")
        self.assertEqual(args.mode, "plan")
        self.assertEqual(args.model, "opus")
        self.assertEqual(args.confidence, "high")
        self.assertEqual(args.output_format, "json")
        self.assertTrue(args.reasons_only)
        self.assertTrue(args.fail_if_empty)
        self.assertTrue(args.summary_only)
        self.assertTrue(args.show_paths)
        self.assertEqual(args.sort, "oldest")

    def test_parse_raw_args_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--limit -1")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--date 2026/04/10")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--since 2026/04/10")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--until 2026/04/10")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--window seven")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--status maybe")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--profile unknown")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--mode draft")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--model turbo")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--confidence unsure")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--format csv")
        with self.assertRaises(ValueError):
            parent_stats.parse_raw_args("--sort random")

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
                    "reason_codes": ["HIGH_RISK_CHANGE", "GREENFIELD_SYSTEM_REQUEST"],
                    "request_text": "Plan a migration for auth",
                },
                {
                    "timestamp": "2026-04-10T09:00:00+00:00",
                    "profile": "parent-no-opus",
                    "selected_model": "sonnet",
                    "selected_mode": "execute",
                    "confidence": "medium",
                    "execution_status": None,
                    "reason_codes": ["SIMPLE_BOUNDED_TASK"],
                    "request_text": "Rename one variable safely",
                },
            ]
            for index, record in enumerate(records):
                (run_dir / f"20260410T0{index}0000Z-parent.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )

            args = parent_stats.StatsArgs(
                limit=2,
                date="2026-04-10",
                since="2026-04-09",
                until="2026-04-10",
                window="7d",
                status="ok",
                profile="parent",
                mode="plan",
                model="opus",
                confidence="high",
                output_format="text",
                sort="newest",
            )
            paths = parent_stats.iter_run_json_files(root, args)
            loaded = parent_stats.load_run_records(paths, args)
            report = parent_stats.format_report(loaded, args)

        self.assertEqual(len(loaded), 1)
        self.assertIn("Status filter: ok", report)
        self.assertIn("Since filter: 2026-04-09", report)
        self.assertIn("Window filter: 7d", report)
        self.assertIn("Until filter: 2026-04-10", report)
        self.assertIn("Profile filter: parent", report)
        self.assertIn("Mode filter: plan", report)
        self.assertIn("Model filter: opus", report)
        self.assertIn("Confidence filter: high", report)
        self.assertIn("Sort order: newest", report)
        self.assertIn("Runs analyzed: 1", report)
        self.assertIn("Status: ok=1", report)
        self.assertIn("Profiles: parent=1", report)
        self.assertIn("Models: opus=1", report)
        self.assertIn(
            "Reason codes: GREENFIELD_SYSTEM_REQUEST=1, HIGH_RISK_CHANGE=1", report
        )
        self.assertIn("Recent runs:", report)
        self.assertIn("Plan a migration for auth", report)
        self.assertNotIn("Rename one variable safely", report)

    def test_format_report_supports_tsv_output(self) -> None:
        records = [
            {
                "timestamp": "2026-04-10T10:00:00+00:00",
                "profile": "parent",
                "selected_model": "opus",
                "selected_mode": "plan",
                "confidence": "high",
                "execution_status": "ok",
                "reason_codes": ["HIGH_RISK_CHANGE"],
                "request_text": "Plan a migration for auth",
            }
        ]
        output = parent_stats.format_report(
            records, parent_stats.StatsArgs(output_format="tsv")
        )
        self.assertIn(
            "timestamp\tprofile\tmodel\tmode\tstatus\tconfidence\treason_codes\trequest_text",
            output,
        )
        self.assertIn(
            "2026-04-10T10:00:00+00:00\tparent\topus\tplan\tok\thigh\tHIGH_RISK_CHANGE\tPlan a migration for auth",
            output,
        )

    def test_format_report_supports_json_output(self) -> None:
        records = [
            {
                "timestamp": "2026-04-10T10:00:00+00:00",
                "profile": "parent",
                "selected_model": "opus",
                "selected_mode": "plan",
                "confidence": "high",
                "execution_status": "ok",
                "reason_codes": ["HIGH_RISK_CHANGE"],
                "request_text": "Plan a migration for auth",
            }
        ]
        output = parent_stats.format_report(
            records, parent_stats.StatsArgs(output_format="json")
        )
        data = json.loads(output)
        self.assertEqual(data["runs_analyzed"], 1)
        self.assertEqual(data["filters"]["sort"], "newest")
        self.assertEqual(data["records"][0]["model"], "opus")
        self.assertEqual(data["records"][0]["reason_codes"], ["HIGH_RISK_CHANGE"])

    def test_format_report_supports_reasons_only_output(self) -> None:
        records = [
            {
                "reason_codes": ["HIGH_RISK_CHANGE", "GREENFIELD_SYSTEM_REQUEST"],
            },
            {
                "reason_codes": ["HIGH_RISK_CHANGE"],
            },
        ]
        output = parent_stats.format_report(
            records,
            parent_stats.StatsArgs(
                date="2026-04-10",
                model="opus",
                reasons_only=True,
            ),
        )
        self.assertIn("Date filter: 2026-04-10", output)
        self.assertIn("Model filter: opus", output)
        self.assertIn("Runs analyzed: 2", output)
        self.assertIn(
            "Reason codes: GREENFIELD_SYSTEM_REQUEST=1, HIGH_RISK_CHANGE=2", output
        )
        self.assertNotIn("Recent runs:", output)

    def test_format_report_supports_summary_only_output(self) -> None:
        records = [
            {
                "timestamp": "2026-04-10T10:00:00+00:00",
                "profile": "parent",
                "selected_model": "opus",
                "selected_mode": "plan",
                "confidence": "high",
                "execution_status": "ok",
                "reason_codes": ["HIGH_RISK_CHANGE"],
                "request_text": "Plan a migration for auth",
                "_source_path": ".parent/runs/2026-04-10/20260410T100000Z-parent.json",
            }
        ]
        output = parent_stats.format_report(
            records,
            parent_stats.StatsArgs(summary_only=True, model="opus", show_paths=True),
        )
        self.assertIn("Model filter: opus", output)
        self.assertIn("Sort order: newest", output)
        self.assertIn("Reason codes: HIGH_RISK_CHANGE=1", output)
        self.assertIn("Included paths:", output)
        self.assertIn("20260410T100000Z-parent.json", output)
        self.assertNotIn("Recent runs:", output)
        self.assertNotIn("Plan a migration for auth", output)

    def test_format_report_supports_reasons_only_json_output(self) -> None:
        records = [
            {"reason_codes": ["HIGH_RISK_CHANGE", "GREENFIELD_SYSTEM_REQUEST"]},
            {"reason_codes": ["HIGH_RISK_CHANGE"]},
        ]
        output = parent_stats.format_report(
            records,
            parent_stats.StatsArgs(output_format="json", reasons_only=True),
        )
        data = json.loads(output)
        self.assertEqual(data["runs_analyzed"], 2)
        self.assertEqual(
            data["reason_codes"],
            {"GREENFIELD_SYSTEM_REQUEST": 1, "HIGH_RISK_CHANGE": 2},
        )
        self.assertNotIn("records", data)
        self.assertTrue(data["filters"]["reasons_only"])
        self.assertFalse(data["filters"]["fail_if_empty"])
        self.assertFalse(data["filters"]["summary_only"])
        self.assertFalse(data["filters"]["show_paths"])

    def test_sort_oldest_prefers_oldest_logs_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            older = run_dir / "20260410T090000Z-parent.json"
            newer = run_dir / "20260410T100000Z-parent.json"
            older.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-10T09:00:00+00:00",
                        "request_text": "Older request",
                    }
                ),
                encoding="utf-8",
            )
            newer.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-10T10:00:00+00:00",
                        "request_text": "Newer request",
                    }
                ),
                encoding="utf-8",
            )
            args = parent_stats.StatsArgs(limit=1, sort="oldest")
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(loaded[0]["request_text"], "Older request")

    def test_since_filter_excludes_older_date_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            older_dir = root / ".parent" / "runs" / "2026-04-09"
            newer_dir = root / ".parent" / "runs" / "2026-04-10"
            older_dir.mkdir(parents=True)
            newer_dir.mkdir(parents=True)
            (older_dir / "20260409T100000Z-parent.json").write_text(
                json.dumps({"request_text": "Older day"}), encoding="utf-8"
            )
            (newer_dir / "20260410T100000Z-parent.json").write_text(
                json.dumps({"request_text": "Newer day"}), encoding="utf-8"
            )
            args = parent_stats.StatsArgs(limit=5, since="2026-04-10")
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["request_text"], "Newer day")

    def test_until_filter_excludes_newer_date_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            older_dir = root / ".parent" / "runs" / "2026-04-09"
            newer_dir = root / ".parent" / "runs" / "2026-04-10"
            older_dir.mkdir(parents=True)
            newer_dir.mkdir(parents=True)
            (older_dir / "20260409T100000Z-parent.json").write_text(
                json.dumps({"request_text": "Older day"}), encoding="utf-8"
            )
            (newer_dir / "20260410T100000Z-parent.json").write_text(
                json.dumps({"request_text": "Newer day"}), encoding="utf-8"
            )
            args = parent_stats.StatsArgs(limit=5, until="2026-04-09")
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["request_text"], "Older day")

    def test_window_filter_excludes_older_directories_before_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            within_dir = root / ".parent" / "runs" / "2026-04-09"
            older_dir = root / ".parent" / "runs" / "2026-04-02"
            within_dir.mkdir(parents=True)
            older_dir.mkdir(parents=True)
            (within_dir / "20260409T100000Z-parent.json").write_text(
                json.dumps({"request_text": "Within window"}), encoding="utf-8"
            )
            (older_dir / "20260402T100000Z-parent.json").write_text(
                json.dumps({"request_text": "Outside window"}), encoding="utf-8"
            )
            with mock.patch.object(
                parent_stats, "current_date", return_value=datetime.date(2026, 4, 10)
            ):
                args = parent_stats.StatsArgs(limit=5, window="2d")
                loaded = parent_stats.load_run_records(
                    parent_stats.iter_run_json_files(root, args), args
                )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["request_text"], "Within window")

    def test_limit_zero_keeps_all_matching_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            for index in range(3):
                (run_dir / f"20260410T{index}00000Z-parent.json").write_text(
                    json.dumps({"request_text": f"Request {index}"}), encoding="utf-8"
                )
            args = parent_stats.StatsArgs(limit=0)
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(len(loaded), 3)

    def test_show_paths_exposes_loaded_file_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            path = run_dir / "20260410T400000Z-parent.json"
            path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-10T10:00:00+00:00",
                        "profile": "parent",
                        "selected_model": "opus",
                        "selected_mode": "plan",
                        "confidence": "high",
                        "execution_status": "ok",
                        "reason_codes": ["HIGH_RISK_CHANGE"],
                        "request_text": "Plan a migration for auth",
                    }
                ),
                encoding="utf-8",
            )
            args = parent_stats.StatsArgs(show_paths=True)
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
            output = parent_stats.format_report(
                loaded, parent_stats.StatsArgs(show_paths=True)
            )
        self.assertIn("Included paths:", output)
        self.assertIn(str(path), output)

    def test_profile_filter_excludes_other_profiles(self) -> None:
        records = [
            {
                "profile": "parent",
                "execution_status": "ok",
                "request_text": "Auth migration",
            },
            {
                "profile": "parent-no-opus",
                "execution_status": "ok",
                "request_text": "Cheap fix",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            for index, record in enumerate(records):
                (run_dir / f"20260410T0{index}0000Z-parent.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )
            args = parent_stats.StatsArgs(profile="parent-no-opus")
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["profile"], "parent-no-opus")

    def test_mode_filter_excludes_other_modes(self) -> None:
        records = [
            {
                "selected_mode": "plan",
                "execution_status": "ok",
                "request_text": "Auth migration",
            },
            {
                "selected_mode": "execute",
                "execution_status": "ok",
                "request_text": "Cheap fix",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            for index, record in enumerate(records):
                (run_dir / f"20260410T1{index}0000Z-parent.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )
            args = parent_stats.StatsArgs(mode="execute")
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["selected_mode"], "execute")

    def test_model_filter_excludes_other_models(self) -> None:
        records = [
            {
                "selected_model": "opus",
                "execution_status": "ok",
                "request_text": "Auth migration",
            },
            {
                "selected_model": "sonnet",
                "execution_status": "ok",
                "request_text": "Cheap fix",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            for index, record in enumerate(records):
                (run_dir / f"20260410T2{index}0000Z-parent.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )
            args = parent_stats.StatsArgs(model="sonnet")
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["selected_model"], "sonnet")

    def test_confidence_filter_excludes_other_confidence_levels(self) -> None:
        records = [
            {
                "confidence": "high",
                "execution_status": "ok",
                "request_text": "Auth migration",
            },
            {
                "confidence": "medium",
                "execution_status": "ok",
                "request_text": "Cheap fix",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_dir = root / ".parent" / "runs" / "2026-04-10"
            run_dir.mkdir(parents=True)
            for index, record in enumerate(records):
                (run_dir / f"20260410T3{index}0000Z-parent.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )
            args = parent_stats.StatsArgs(confidence="medium")
            loaded = parent_stats.load_run_records(
                parent_stats.iter_run_json_files(root, args), args
            )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["confidence"], "medium")

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

    def test_main_fails_when_empty_results_are_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                parent_stats.os.environ,
                {"PARENTS_PROJECT_ROOT": tmpdir},
                clear=False,
            ):
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    exit_code = parent_stats.main(
                        ["parent_stats.py", "--date", "2026-04-10", "--fail-if-empty"]
                    )
        self.assertEqual(exit_code, 1)
        self.assertIn("No run logs found.", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
