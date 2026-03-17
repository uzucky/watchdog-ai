"""Webhook notifier for Slack/Discord."""

import json

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    from urllib2 import urlopen, Request, URLError


ICONS = {"healthy": "OK", "warning": "WARNING", "critical": "CRITICAL"}


def send_webhook(url, results, project="watchdog"):
    """Send check results to a webhook URL (Slack/Discord compatible)."""
    failures = [r for r in results if r.status != "healthy"]
    if not failures:
        return  # only notify on problems

    lines = []
    for r in failures:
        icon = ICONS.get(r.status, "???")
        lines.append("[{}] {} -- {}".format(icon, r.name, r.message))

    text = "*{}: {} issue(s)*\n{}".format(project, len(failures), "\n".join(lines))

    payload = json.dumps({"text": text}).encode("utf-8")

    try:
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        urlopen(req, timeout=10)
    except Exception:
        pass  # don't crash on notification failure
