from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "install_global_commands.py"
)
SPEC = importlib.util.spec_from_file_location("install_global_commands", MODULE_PATH)
install_global_commands = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = install_global_commands
SPEC.loader.exec_module(install_global_commands)


class InstallGlobalCommandsTests(unittest.TestCase):
    def test_parent_command_body_keeps_session_placeholders(self) -> None:
        body = install_global_commands.command_body("/parent", "desc")
        self.assertIn(
            '--session-id "${CLAUDE_SESSION_ID}" --command-name "/parent"', body
        )

    def test_parent_stats_command_body_omits_router_only_flags(self) -> None:
        body = install_global_commands.command_body(
            "/parent-stats",
            "desc",
            script_path=install_global_commands.STATS_SCRIPT_PATH,
            script_args="",
        )
        self.assertNotIn("--session-id", body)
        self.assertNotIn("--command-name", body)
        self.assertIn(str(install_global_commands.STATS_SCRIPT_PATH), body)


if __name__ == "__main__":
    unittest.main()
