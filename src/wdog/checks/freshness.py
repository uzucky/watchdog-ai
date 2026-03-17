"""Freshness check - was a file or endpoint updated recently?"""

import json
import os
import time

from wdog.checks.base import BaseCheck


def parse_duration(s):
    """Parse duration string like '2h', '30m', '1d' to seconds."""
    s = s.strip().lower()
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if s[-1] in multipliers:
        try:
            return float(s[:-1]) * multipliers[s[-1]]
        except ValueError:
            pass
    try:
        return float(s)
    except ValueError:
        raise ValueError("Invalid duration: '{}'. Use format like '2h', '30m', '1d'".format(s))


class FreshnessCheck(BaseCheck):
    """Check if a file was modified recently.

    Config:
        path: str - file path to check
        max_age: str - maximum age like "2h", "30m", "1d"
        json_field: str - optional, check a timestamp field inside JSON
    """

    def run(self):
        path = self.config.get("path", "")
        max_age_str = self.config.get("max_age", "24h")

        try:
            max_age_secs = parse_duration(max_age_str)
        except ValueError as e:
            return self._fail(str(e))

        # Resolve relative paths
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            config_dir = self.config.get("_config_dir", ".")
            path = os.path.join(config_dir, path)

        if not os.path.exists(path):
            return self._fail("File not found: {}".format(path))

        # Check file modification time
        mtime = os.path.getmtime(path)
        age_secs = time.time() - mtime
        age_human = _format_age(age_secs)

        # Optionally check a JSON timestamp field
        json_field = self.config.get("json_field")
        if json_field:
            return self._check_json_field(path, json_field, max_age_secs)

        max_age_human = _format_age(max_age_secs)
        if age_secs <= max_age_secs:
            return self._healthy(
                "Updated {} ago (limit: {})".format(age_human, max_age_human),
                {"age_seconds": round(age_secs), "max_age_seconds": max_age_secs},
            )
        else:
            return self._fail(
                "Stale: last updated {} ago (limit: {})".format(age_human, max_age_human),
                {"age_seconds": round(age_secs), "max_age_seconds": max_age_secs},
            )

    def _check_json_field(self, path, field, max_age_secs):
        """Check a timestamp field inside a JSON file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return self._fail("Cannot read JSON: {}".format(e))

        value = _resolve_path(data, field)
        if value is None:
            return self._fail("Field '{}' not found in JSON".format(field))

        # Try to parse as ISO timestamp
        from wdog.util.time import parse_timestamp
        ts = parse_timestamp(str(value))
        if ts is None:
            return self._fail("Cannot parse '{}' as timestamp: {}".format(field, value))

        age_secs = time.time() - ts
        age_human = _format_age(age_secs)
        max_age_human = _format_age(max_age_secs)

        if age_secs <= max_age_secs:
            return self._healthy(
                "Field '{}' updated {} ago".format(field, age_human),
                {"age_seconds": round(age_secs)},
            )
        else:
            return self._fail(
                "Field '{}' stale: {} ago (limit: {})".format(field, age_human, max_age_human),
                {"age_seconds": round(age_secs)},
            )


def _resolve_path(data, path):
    """Resolve a dotted path like 'foo.bar.baz' or '$.foo.bar' in a dict."""
    if path.startswith("$."):
        path = path[2:]
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _format_age(seconds):
    """Format seconds as human-readable duration."""
    if seconds < 60:
        return "{:.0f}s".format(seconds)
    elif seconds < 3600:
        return "{:.0f}m".format(seconds / 60)
    elif seconds < 86400:
        return "{:.1f}h".format(seconds / 3600)
    else:
        return "{:.1f}d".format(seconds / 86400)
