from __future__ import annotations

import importlib.util
import io
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
    @staticmethod
    def make_transcript_entries(count: int) -> list[dict]:
        entries: list[dict] = []
        for idx in range(count):
            if idx % 2 == 0:
                entries.append(
                    {"type": "user", "message": {"content": f"user message {idx}"}}
                )
            else:
                entries.append(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {"type": "text", "text": f"assistant message {idx}"}
                            ]
                        },
                    }
                )
        return entries

    def test_parse_command_arguments(self) -> None:
        parsed = parent.parse_command_arguments(
            "--model sonnet --mode execute --effort high --why fix auth flow"
        )
        self.assertEqual(parsed.model, "sonnet")
        self.assertEqual(parsed.mode, "execute")
        self.assertEqual(parsed.effort, "high")
        self.assertTrue(parsed.why)
        self.assertEqual(parsed.task, "fix auth flow")

    def test_load_request_text_prefers_stdin_but_still_uses_session_for_anchor(
        self,
    ) -> None:
        cli_args = mock.Mock(
            session_id="session", command_name="/parent", started_at=None
        )
        with (
            mock.patch.object(
                sys, "stdin", io.StringIO("--dry-run rename one variable")
            ),
            mock.patch.object(
                parent, "find_anchor_index_from_session_once", return_value=7
            ),
        ):
            anchor_index, raw_request = parent.load_request_text(cli_args, [])
        self.assertEqual(anchor_index, 7)
        self.assertEqual(raw_request, "--dry-run rename one variable")

    def test_load_request_text_keeps_working_without_session_anchor(self) -> None:
        cli_args = mock.Mock(
            session_id="session", command_name="/parent", started_at=None
        )
        with (
            mock.patch.object(
                sys, "stdin", io.StringIO("--dry-run rename one variable")
            ),
            mock.patch.object(
                parent, "find_anchor_index_from_session_once", return_value=-1
            ),
        ):
            anchor_index, raw_request = parent.load_request_text(cli_args, [])
        self.assertEqual(anchor_index, -1)
        self.assertEqual(raw_request, "--dry-run rename one variable")

    def test_load_request_text_does_not_poll_session_when_stdin_is_already_available(
        self,
    ) -> None:
        cli_args = mock.Mock(
            session_id="session", command_name="/parent", started_at=None
        )
        with (
            mock.patch.object(sys, "stdin", io.StringIO("rename one variable")),
            mock.patch.object(
                parent, "find_anchor_index_from_session_once", return_value=-1
            ) as find_anchor,
            mock.patch.object(parent, "extract_prompt_from_session") as extract_prompt,
        ):
            anchor_index, raw_request = parent.load_request_text(cli_args, [])
        self.assertEqual(anchor_index, -1)
        self.assertEqual(raw_request, "rename one variable")
        find_anchor.assert_called_once()
        extract_prompt.assert_not_called()

    def test_parent_uses_opus_for_architecture_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments(
                "Design a new authentication architecture with migration planning"
            )
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            self.assertEqual(decision.selected_model, "opus")
            self.assertEqual(decision.selected_mode, "plan")
            self.assertEqual(decision.effective_effort, "max")

    def test_parent_no_opus_downgrades_to_sonnet_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments(
                "Design a new authentication architecture with migration planning"
            )
            decision = parent.choose_route(
                parent.PROFILES["parent-no-opus"], parsed, root
            )
            self.assertEqual(decision.selected_model, "sonnet")
            self.assertEqual(decision.selected_mode, "plan")
            self.assertIn("PROFILE_NO_OPUS", decision.reason_codes)

    def test_effort_clamps_for_haiku(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments(
                "--model haiku --effort max rename one variable"
            )
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            self.assertEqual(decision.selected_model, "haiku")
            self.assertEqual(decision.selected_effort, "max")
            self.assertEqual(decision.effective_effort, "medium")
            self.assertIn("EFFORT_CLAMPED_BY_MODEL", decision.reason_codes)

    def test_no_opus_rejects_opus_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("--model opus implement the task")
            with self.assertRaisesRegex(
                ValueError, r"retry with `/parent --model opus implement the task`"
            ):
                parent.choose_route(parent.PROFILES["parent-no-opus"], parsed, root)

    def test_haiku_plan_error_includes_recovery_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments(
                "--model haiku --mode plan design an auth migration"
            )
            with self.assertRaisesRegex(
                ValueError,
                r"Retry with `--model sonnet`, `--model opus`, or switch to `--mode execute`",
            ):
                parent.choose_route(parent.PROFILES["parent"], parsed, root)

    def test_low_confidence_forces_safe_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
            parsed = parent.parse_command_arguments(
                "Help me improve the whole system somehow"
            )
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            self.assertEqual(decision.selected_model, "sonnet")
            self.assertEqual(decision.selected_mode, "plan")
            self.assertIn("LOW_CONFIDENCE_SAFE_FALLBACK", decision.reason_codes)

    def test_explain_decision_mentions_low_confidence_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
            parsed = parent.parse_command_arguments(
                "Help me improve the whole system somehow"
            )
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
        message = parent.explain_decision(parent.PROFILES["parent"], decision)
        self.assertIn("broad or ambiguous enough", message)
        self.assertIn("direct execution path would be risky", message)

    def test_execute_route_only_runs_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("rename one variable")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            completed = mock.Mock(returncode=1, stdout="", stderr="boom")
            with mock.patch.object(
                parent, "run_command", return_value=completed
            ) as run_command:
                result = parent.execute_route(decision, root, "")
            self.assertFalse(result.ok)
            self.assertEqual(run_command.call_count, 1)

    def test_format_failure_includes_execute_recovery_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("rename one variable")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
        result = parent.ExecutionResult(ok=False, stdout="", stderr="boom", exit_code=1)
        message = parent.format_failure(decision, result)
        self.assertIn("Route:", message)
        self.assertIn("Next step: retry with `--mode plan`", message)

    def test_format_failure_includes_plan_recovery_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments(
                "Plan a migration for the production auth system"
            )
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
        result = parent.ExecutionResult(ok=False, stdout="", stderr="boom", exit_code=1)
        message = parent.format_failure(decision, result)
        self.assertIn("Route:", message)
        self.assertIn("Next step: retry with `--dry-run --why`", message)

    def test_main_shows_concrete_retry_guidance_when_request_capture_fails(
        self,
    ) -> None:
        cli_args = mock.Mock(
            session_id=None,
            command_name="/parent",
            command_profile=None,
            started_at=None,
        )
        with (
            mock.patch.object(parent, "parse_cli_args", return_value=(cli_args, [])),
            mock.patch.object(sys, "stdin", io.StringIO("")),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            exit_code = parent.main(["parent.py"])
        self.assertEqual(exit_code, 2)
        output = stdout.getvalue()
        self.assertIn("Could not capture the current command arguments.", output)
        self.assertIn("/parent fix the flaky integration test", output)

    def test_main_prepends_low_confidence_transition_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
            result = parent.ExecutionResult(
                ok=True,
                stdout="plan output",
                stderr="",
                exit_code=0,
                argv=[],
            )
            cli_args = mock.Mock(
                session_id=None,
                command_name="/parent",
                command_profile=None,
                started_at=None,
            )
            with (
                mock.patch.dict(
                    parent.os.environ, {"PARENTS_PROJECT_ROOT": str(root)}, clear=False
                ),
                mock.patch.object(
                    sys,
                    "stdin",
                    io.StringIO("Help me improve the whole system somehow"),
                ),
                mock.patch.object(
                    parent, "parse_cli_args", return_value=(cli_args, [])
                ),
                mock.patch.object(parent, "execute_route", return_value=result),
                mock.patch.object(parent, "write_logs"),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                exit_code = parent.main(["parent.py"])
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("I started with a plan", output)
        self.assertIn("plan output", output)

    def test_main_prepends_parent_no_opus_transition_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = parent.ExecutionResult(
                ok=True,
                stdout="plan output",
                stderr="",
                exit_code=0,
                argv=[],
            )
            cli_args = mock.Mock(
                session_id=None,
                command_name="/parent-no-opus",
                command_profile=None,
                started_at=None,
            )
            with (
                mock.patch.dict(
                    parent.os.environ, {"PARENTS_PROJECT_ROOT": str(root)}, clear=False
                ),
                mock.patch.object(
                    sys,
                    "stdin",
                    io.StringIO(
                        "Design a new authentication architecture with migration planning"
                    ),
                ),
                mock.patch.object(
                    parent, "parse_cli_args", return_value=(cli_args, [])
                ),
                mock.patch.object(parent, "execute_route", return_value=result),
                mock.patch.object(parent, "write_logs"),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                exit_code = parent.main(["parent.py"])
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("I stayed on Sonnet and started with a plan", output)
        self.assertIn("plan output", output)

    def test_main_prepends_effort_clamp_hint_for_model_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = parent.ExecutionResult(
                ok=True,
                stdout="child output",
                stderr="",
                exit_code=0,
                argv=[],
            )
            cli_args = mock.Mock(
                session_id=None,
                command_name="/parent",
                command_profile=None,
                started_at=None,
            )
            with (
                mock.patch.dict(
                    parent.os.environ, {"PARENTS_PROJECT_ROOT": str(root)}, clear=False
                ),
                mock.patch.object(
                    sys,
                    "stdin",
                    io.StringIO("--model haiku --effort max rename one variable"),
                ),
                mock.patch.object(
                    parent, "parse_cli_args", return_value=(cli_args, [])
                ),
                mock.patch.object(parent, "execute_route", return_value=result),
                mock.patch.object(parent, "write_logs"),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                exit_code = parent.main(["parent.py"])
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("I adjusted the requested effort from max to medium", output)
        self.assertIn("child output", output)

    def test_main_prepends_effort_clamp_hint_for_mode_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = parent.ExecutionResult(
                ok=True,
                stdout="child output",
                stderr="",
                exit_code=0,
                argv=[],
            )
            cli_args = mock.Mock(
                session_id=None,
                command_name="/parent",
                command_profile=None,
                started_at=None,
            )
            with (
                mock.patch.dict(
                    parent.os.environ, {"PARENTS_PROJECT_ROOT": str(root)}, clear=False
                ),
                mock.patch.object(
                    sys,
                    "stdin",
                    io.StringIO("--mode plan --effort low design an auth migration"),
                ),
                mock.patch.object(
                    parent, "parse_cli_args", return_value=(cli_args, [])
                ),
                mock.patch.object(parent, "execute_route", return_value=result),
                mock.patch.object(parent, "write_logs"),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                exit_code = parent.main(["parent.py"])
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("I adjusted the requested effort from low to high", output)
        self.assertIn("child output", output)

    def test_main_prepends_forced_route_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = parent.ExecutionResult(
                ok=True,
                stdout="child output",
                stderr="",
                exit_code=0,
                argv=[],
            )
            cli_args = mock.Mock(
                session_id=None,
                command_name="/parent",
                command_profile=None,
                started_at=None,
            )
            with (
                mock.patch.dict(
                    parent.os.environ, {"PARENTS_PROJECT_ROOT": str(root)}, clear=False
                ),
                mock.patch.object(
                    sys,
                    "stdin",
                    io.StringIO("--model sonnet --mode execute rename one variable"),
                ),
                mock.patch.object(
                    parent, "parse_cli_args", return_value=(cli_args, [])
                ),
                mock.patch.object(parent, "execute_route", return_value=result),
                mock.patch.object(parent, "write_logs"),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                exit_code = parent.main(["parent.py"])
        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("Using your requested model sonnet, mode execute.", output)
        self.assertIn("child output", output)

    def test_plan_route_uses_read_only_tools_without_claude_plan_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments(
                "Plan a migration for the production auth system"
            )
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            completed = mock.Mock(returncode=0, stdout="ok", stderr="")
            with mock.patch.object(
                parent, "run_command", return_value=completed
            ) as run_command:
                parent.execute_route(decision, root, "")
            argv = run_command.call_args.args[0]
            self.assertIn("--permission-mode", argv)
            self.assertIn("auto", argv)
            self.assertNotIn("plan", argv)
            self.assertIn("Read,Grep,Glob", argv)

    def test_child_prompt_is_sent_via_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments("rename one variable")
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            completed = mock.Mock(returncode=0, stdout="ok", stderr="")
            with mock.patch.object(
                parent, "run_command", return_value=completed
            ) as run_command:
                parent.execute_route(decision, root, "User: earlier context")
            argv = run_command.call_args.args[0]
            self.assertEqual(argv[0], str(parent.CLAUDE_BIN))
            self.assertEqual(argv[1], "-p")
            self.assertNotIn("rename one variable", " ".join(argv))
            self.assertEqual(
                run_command.call_args.kwargs["input_text"],
                parent.build_child_prompt(decision, "User: earlier context"),
            )

    def test_build_recent_context_skips_summary_when_message_count_is_within_limit(
        self,
    ) -> None:
        entries = self.make_transcript_entries(parent.VISIBLE_TRANSCRIPT_MAX_MESSAGES)
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch.object(parent, "load_session_entries", return_value=entries),
            mock.patch.object(parent, "run_command") as run_command,
        ):
            context = parent.build_recent_context(Path(tmpdir), "session", len(entries))
        self.assertIn("user message 0", context)
        self.assertIn(f"assistant message {len(entries) - 1}", context)
        self.assertNotIn("Summary of earlier conversation:", context)
        run_command.assert_not_called()

    def test_build_recent_context_summarizes_older_messages_with_haiku(self) -> None:
        entries = self.make_transcript_entries(
            parent.VISIBLE_TRANSCRIPT_MAX_MESSAGES + 6
        )
        completed = mock.Mock(returncode=0, stdout="- goal\n- decision", stderr="")
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch.object(parent, "load_session_entries", return_value=entries),
            mock.patch.object(
                parent, "run_command", return_value=completed
            ) as run_command,
        ):
            context = parent.build_recent_context(Path(tmpdir), "session", len(entries))
        self.assertIn("Summary of earlier conversation:", context)
        self.assertIn("- goal", context)
        self.assertIn("Recent conversation:", context)
        self.assertIn(f"assistant message {len(entries) - 1}", context)
        self.assertNotIn("user message 0", context)
        argv = run_command.call_args.args[0]
        self.assertEqual(argv[0], str(parent.CLAUDE_BIN))
        self.assertIn("haiku", argv)
        self.assertIn("--tools", argv)
        self.assertEqual(
            run_command.call_args.kwargs["input_text"].count("user message"), 3
        )

    def test_build_recent_context_falls_back_to_latest_transcript_when_anchor_missing(
        self,
    ) -> None:
        entries = self.make_transcript_entries(6)
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            mock.patch.object(parent, "load_session_entries", return_value=entries),
            mock.patch.object(parent, "run_command") as run_command,
        ):
            context = parent.build_recent_context(Path(tmpdir), "session", -1)
        self.assertIn("user message 0", context)
        self.assertIn("assistant message 5", context)
        run_command.assert_not_called()

    def test_write_logs_includes_child_permission_mode_and_tools_in_markdown(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parsed = parent.parse_command_arguments(
                "Plan a migration for the production auth system"
            )
            decision = parent.choose_route(parent.PROFILES["parent"], parsed, root)
            result = parent.ExecutionResult(
                ok=True,
                stdout="plan output",
                stderr="",
                exit_code=0,
                argv=[
                    str(parent.CLAUDE_BIN),
                    "-p",
                    "--model",
                    decision.selected_model,
                    "--effort",
                    decision.effective_effort,
                    "--permission-mode",
                    "auto",
                    "--tools",
                    "Read,Grep,Glob",
                ],
            )

            parent.write_logs(
                root, parent.PROFILES["parent"], "/parent", parsed, decision, result
            )

            run_dir = (
                root
                / parent.RUNS_DIR
                / parent.datetime.now(parent.timezone.utc).strftime("%Y-%m-%d")
            )
            markdown_files = list(run_dir.glob("*.md"))
            self.assertEqual(len(markdown_files), 1)
            markdown = markdown_files[0].read_text(encoding="utf-8")
            self.assertIn("- Child permission mode: `auto`", markdown)
            self.assertIn("- Child tools: `Read,Grep,Glob`", markdown)


if __name__ == "__main__":
    unittest.main()
