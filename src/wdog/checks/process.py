"""Process check - is a process/service running?"""

import subprocess
import sys

from wdog.checks.base import BaseCheck


class ProcessCheck(BaseCheck):
    """Check if a process or service is running.

    Config:
        match: str - process name/pattern to grep in ps output
        platform: str - "auto" (default), "launchd", "systemd", or "ps"
    """

    def run(self):
        match = self.config.get("match", "")
        platform = self.config.get("platform", "auto")

        if platform == "auto":
            if sys.platform == "darwin":
                platform = "launchd"
            else:
                platform = "ps"

        if platform == "launchd":
            return self._check_launchd(match)
        elif platform == "systemd":
            return self._check_systemd(match)
        else:
            return self._check_ps(match)

    def _check_launchd(self, label):
        """Check macOS launchd service by label."""
        try:
            out = subprocess.check_output(
                ["launchctl", "list"],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="replace")
        except (subprocess.CalledProcessError, FileNotFoundError):
            return self._check_ps(label)

        for line in out.strip().split("\n"):
            if label in line:
                parts = line.split("\t")
                if len(parts) >= 3:
                    pid = parts[0].strip()
                    exit_code = parts[1].strip()
                    if pid != "-" and pid.isdigit():
                        return self._healthy(
                            "Running (PID {})".format(pid),
                            {"pid": int(pid), "exit_code": exit_code},
                        )
                    elif exit_code != "0":
                        return self._fail(
                            "Not running (exit code {})".format(exit_code),
                            {"exit_code": exit_code},
                        )
                    else:
                        return self._healthy(
                            "Registered (not currently active)",
                            {"exit_code": exit_code},
                        )

        return self._fail("Service '{}' not found in launchctl".format(label))

    def _check_systemd(self, unit):
        """Check Linux systemd service."""
        try:
            out = subprocess.check_output(
                ["systemctl", "is-active", unit],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="replace").strip()
        except subprocess.CalledProcessError as e:
            out = e.output.decode("utf-8", errors="replace").strip() if e.output else "unknown"
        except FileNotFoundError:
            return self._check_ps(unit)

        if out == "active":
            return self._healthy("Active (systemd)")
        else:
            return self._fail("systemd status: {}".format(out))

    def _check_ps(self, pattern):
        """Fallback: grep ps output for pattern."""
        try:
            out = subprocess.check_output(
                ["ps", "aux"],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="replace")
        except (subprocess.CalledProcessError, FileNotFoundError):
            return self._fail("Cannot run 'ps aux'")

        matches = []
        for line in out.strip().split("\n"):
            if pattern in line and "wdog" not in line and "grep" not in line:
                matches.append(line.strip())

        if matches:
            return self._healthy(
                "Found {} process(es)".format(len(matches)),
                {"matches": matches[:5]},
            )
        else:
            return self._fail("No process matching '{}'".format(pattern))
