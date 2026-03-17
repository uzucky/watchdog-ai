"""Custom script check - run a user script and check exit code."""

import os
import subprocess

from wdog.checks.base import BaseCheck


class CustomCheck(BaseCheck):
    """Run a custom script. Exit 0 = healthy, 1 = warning, 2 = critical.

    Config:
        command: str - command to run
        timeout: int - timeout in seconds (default 30)
    """

    def run(self):
        command = self.config.get("command", "")
        timeout = self.config.get("timeout", 30)

        if not command:
            return self._fail("No command specified")

        config_dir = self.config.get("_config_dir", ".")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                cwd=config_dir,
            )
        except subprocess.TimeoutExpired:
            return self._fail(
                "Script timed out after {}s".format(timeout),
                {"command": command},
            )
        except Exception as e:
            return self._fail(
                "Script error: {}".format(e),
                {"command": command},
            )

        stdout = result.stdout.decode("utf-8", errors="replace").strip()[:500]
        stderr = result.stderr.decode("utf-8", errors="replace").strip()[:500]
        code = result.returncode

        detail = {
            "command": command,
            "exit_code": code,
            "stdout": stdout,
            "stderr": stderr,
        }

        if code == 0:
            return self._healthy(stdout or "Script passed", detail)
        elif code == 1:
            return self._result("warning", stdout or "Script warning", detail)
        else:
            return self._result("critical", stdout or "Script failed (exit {})".format(code), detail)
