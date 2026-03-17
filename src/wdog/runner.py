"""Main check execution engine."""

import json
import sys
import time

from wdog.checks import create_check
from wdog.notify.terminal import format_results
from wdog.notify.webhook import send_webhook


def run_checks(config, output_format="terminal"):
    """Run all checks from config and return results + exit code."""
    checks_config = config.get("checks", [])
    results = []

    for check_config in checks_config:
        try:
            check = create_check(check_config)
            result = check.run()
        except Exception as e:
            from wdog.checks.base import CheckResult
            result = CheckResult(
                name=check_config.get("name", "unknown"),
                status="critical",
                message="Check error: {}".format(e),
            )
        results.append(result)

    # Output
    if output_format == "json":
        output = {
            "project": config.get("project", ""),
            "results": [r.to_dict() for r in results],
            "summary": {
                "total": len(results),
                "healthy": sum(1 for r in results if r.status == "healthy"),
                "warning": sum(1 for r in results if r.status == "warning"),
                "critical": sum(1 for r in results if r.status == "critical"),
            },
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_results(results))

    # Notify
    notify_configs = config.get("notify", [])
    for nc in notify_configs:
        ntype = nc.get("type", "")
        if ntype == "webhook":
            url = nc.get("url", "")
            if url:
                on_statuses = nc.get("on", ["critical", "warning"])
                filtered = [r for r in results if r.status in on_statuses]
                if filtered:
                    send_webhook(url, filtered, config.get("project", "watchdog"))

    # Exit code: 0=healthy, 1=warning, 2=critical
    has_critical = any(r.status == "critical" for r in results)
    has_warning = any(r.status == "warning" for r in results)
    if has_critical:
        return 2
    elif has_warning:
        return 1
    return 0


def run_daemon(config, output_format="terminal"):
    """Run checks on a schedule."""
    from wdog.checks.freshness import parse_duration
    interval_str = config.get("interval", "5m")
    try:
        interval_secs = parse_duration(interval_str)
    except ValueError:
        interval_secs = 300

    print("Watchdog daemon started (interval: {})".format(interval_str))
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            run_checks(config, output_format)
        except Exception as e:
            print("Error: {}".format(e))

        try:
            time.sleep(interval_secs)
        except KeyboardInterrupt:
            print("\nWatchdog stopped.")
            break
