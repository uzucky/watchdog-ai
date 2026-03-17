"""Terminal output notifier with ANSI colors."""

import sys


# ANSI color codes
COLORS = {
    "healthy": "\033[32m",   # green
    "warning": "\033[33m",   # yellow
    "critical": "\033[31m",  # red
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}

ICONS = {
    "healthy": "OK",
    "warning": "WARN",
    "critical": "CRIT",
}


def supports_color():
    """Check if terminal supports ANSI colors."""
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()


def format_results(results, use_color=None):
    """Format check results for terminal output."""
    if use_color is None:
        use_color = supports_color()

    lines = []
    counts = {"healthy": 0, "warning": 0, "critical": 0}

    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
        icon = ICONS.get(r.status, "???")

        if use_color:
            color = COLORS.get(r.status, "")
            reset = COLORS["reset"]
            line = "  {}{:>4}{} {} -- {}".format(color, icon, reset, r.name, r.message)
        else:
            line = "  [{:>4}] {} -- {}".format(icon, r.name, r.message)

        lines.append(line)

    # Header
    total = len(results)
    header = "Watchdog: {} check(s)".format(total)
    if counts["critical"] > 0:
        status_summary = "{} critical, {} warning, {} healthy".format(
            counts["critical"], counts["warning"], counts["healthy"])
    elif counts["warning"] > 0:
        status_summary = "{} warning, {} healthy".format(
            counts["warning"], counts["healthy"])
    else:
        status_summary = "all healthy"

    output = []
    output.append("")
    if use_color:
        output.append("{}{}{}  ({})".format(COLORS["bold"], header, COLORS["reset"], status_summary))
    else:
        output.append("{}  ({})".format(header, status_summary))
    output.append("")
    output.extend(lines)
    output.append("")

    return "\n".join(output)
