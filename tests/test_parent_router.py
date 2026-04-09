from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "parent.py"
SPEC = importlib.util.spec_from_file_location("parent_router", MODULE_PATH)
parent = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = parent
SPEC.loader.exec_module(parent)


class ParentRouterTests(unittest.TestCase):
    def test_parse_command_arguments(self) -> None:
        parsed = parent.parse_command_arguments("--model sonnet --mode execute --effort high --why fix auth flow")
        self.assertEqual(parsed.model, "sonnet")
        self.assertEqual(parsed.mode, "execute")
        self.assertEqual(parsed.effort, "high")
        self.assertTrue(parsed.why)
        self.assertEqual(parsed.task, "fix auth flow")

    def test_parent_uses_opus_for_architecture_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("Design a new authentication architecture with migration planning")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            self.assertEqual(decision.selected_model, "opus")
            self.assertEqual(decision.selected_mode, "plan")
            self.assertEqual(decision.effective_effort, "max")

    def test_parent_no_opus_downgrades_to_sonnet_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("Design a new authentication architecture with migration planning")
            decision = parent.choose_route(parent.PROFILES["parent-no-opus"], parsed, root)
            self.assertEqual(decision.selected_model, "sonnet")
            self.assertEqual(decision.selected_mode, "plan")
            self.assertIn("PROFILE_NO_OPUS", decision.reason_codes)

    def test_effort_clamps_for_haiku(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("--model haiku --effort max rename one variable")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            self.assertEqual(decision.selected_model, "haiku")
            self.assertEqual(decision.selected_effort, "max")
            self.assertEqual(decision.effective_effort, "medium")
            self.assertIn("EFFORT_CLAMPED_BY_MODEL", decision.reason_codes)

    def test_no_opus_rejects_opus_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("--model opus implement the task")
            with self.assertRaises(ValueError):
                parent.choose_route(parent.PROFILES["parent-no-opus"], parsed, root)

    def test_low_confidence_forces_safe_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
            parsed = parent.parse_command_arguments("Help me improve the whole system somehow")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            self.assertEqual(decision.selected_model, "sonnet")
            self.assertEqual(decision.selected_mode, "plan")
            self.assertIn("LOW_CONFIDENCE_SAFE_FALLBACK", decision.reason_codes)

    def test_execute_route_only_runs_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("rename one variable")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            completed = mock.Mock(returncode=1, stdout="", stderr="boom")
            with mock.patch.object(parent, "run_command", return_value=completed) as run_command:
                result = parent.execute_route(decision, root, "")
            self.assertFalse(result.ok)
            self.assertEqual(run_command.call_count, 1)

    def test_plan_route_uses_read_only_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("Plan a migration for the production auth system")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            completed = mock.Mock(returncode=0, stdout="ok", stderr="")
            with mock.patch.object(parent, "run_command", return_value=completed) as run_command:
                parent.execute_route(decision, root, "")
            argv = run_command.call_args.args[0]
            self.assertIn("--permission-mode", argv)
            self.assertIn("plan", argv)
            self.assertIn("Read,Grep,Glob", argv)


if __name__ == "__main__":
    unittest.main()
