"""Log scan check - detect error patterns in log files."""

import os
import re

from wdog.checks.base import BaseCheck


class LogScanCheck(BaseCheck):
    """Scan log files for error patterns.

    Config:
        path: str - log file path
        patterns: list[str] - regex patterns to search for
        tail: int - number of lines to scan from end (default 50)
        threshold: int - alert if >= this many matches (default 1)
    """

    def run(self):
        path = self.config.get("path", "")
        patterns = self.config.get("patterns", [])
        tail_lines = self.config.get("tail", 50)
        threshold = self.config.get("threshold", 1)

        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            config_dir = self.config.get("_config_dir", ".")
            path = os.path.join(config_dir, path)

        if not os.path.exists(path):
            return self._fail("Log file not found: {}".format(path))

        if not patterns:
            return self._healthy("No patterns configured")

        # Read last N lines
        try:
            lines = _tail(path, tail_lines)
        except IOError as e:
            return self._fail("Cannot read log: {}".format(e))

        # Compile patterns
        compiled = []
        for p in patterns:
            try:
                compiled.append((p, re.compile(p, re.IGNORECASE)))
            except re.error:
                compiled.append((p, None))

        # Scan
        total_matches = 0
        matched_lines = []
        pattern_counts = {}

        for line in lines:
            for pattern_str, regex in compiled:
                if regex and regex.search(line):
                    total_matches += 1
                    pattern_counts[pattern_str] = pattern_counts.get(pattern_str, 0) + 1
                    if len(matched_lines) < 5:
                        matched_lines.append(line.strip()[:200])
                    break  # one match per line is enough

        detail = {
            "total_matches": total_matches,
            "threshold": threshold,
            "lines_scanned": len(lines),
            "pattern_counts": pattern_counts,
        }

        if total_matches >= threshold:
            return self._fail(
                "{} error(s) found in last {} lines (threshold: {})".format(
                    total_matches, len(lines), threshold),
                dict(detail, matched_lines=matched_lines),
            )
        else:
            return self._healthy(
                "{} match(es) in {} lines (threshold: {})".format(
                    total_matches, len(lines), threshold),
                detail,
            )


def _tail(path, n):
    """Read last n lines of a file efficiently."""
    lines = []
    with open(path, "rb") as f:
        # Seek to end
        f.seek(0, 2)
        size = f.tell()
        if size == 0:
            return []

        # Read in chunks from end
        chunk_size = min(8192, size)
        pos = size
        remaining = ""

        while pos > 0 and len(lines) < n + 1:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            chunk = f.read(read_size).decode("utf-8", errors="replace")
            remaining = chunk + remaining
            lines = remaining.split("\n")

    # Return last n non-empty lines
    return [l for l in lines[-n:] if l.strip()]
