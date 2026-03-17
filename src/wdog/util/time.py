"""Timestamp parsing utilities."""

import calendar
import re
from datetime import datetime


def parse_timestamp(s):
    """Parse an ISO-ish timestamp string to Unix epoch seconds.
    Returns None if parsing fails."""
    s = s.strip()

    # ISO 8601 variants
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    # Strip timezone suffix like +00:00
    s_clean = re.sub(r"[+-]\d{2}:\d{2}$", "", s)

    for fmt in formats:
        try:
            dt = datetime.strptime(s_clean, fmt)
            return calendar.timegm(dt.timetuple()) + dt.microsecond / 1e6
        except ValueError:
            continue

    # Try Unix timestamp
    try:
        ts = float(s)
        if ts > 1e9:  # plausible epoch
            return ts
    except ValueError:
        pass

    return None
