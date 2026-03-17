"""Check type registry."""

from wdog.checks.process import ProcessCheck
from wdog.checks.freshness import FreshnessCheck
from wdog.checks.log_scan import LogScanCheck
from wdog.checks.assertion import AssertionCheck
from wdog.checks.http import HttpCheck
from wdog.checks.custom import CustomCheck

REGISTRY = {
    "process": ProcessCheck,
    "freshness": FreshnessCheck,
    "log_scan": LogScanCheck,
    "assertion": AssertionCheck,
    "http": HttpCheck,
    "script": CustomCheck,
}


def create_check(config):
    """Create a check instance from config dict."""
    check_type = config.get("type")
    if check_type not in REGISTRY:
        raise ValueError("Unknown check type: {}. Available: {}".format(
            check_type, ", ".join(sorted(REGISTRY.keys()))))
    return REGISTRY[check_type](config)
