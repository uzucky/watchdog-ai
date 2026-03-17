"""CLI entry point for wdog."""

import argparse
import os
import sys

from wdog import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="wdog",
        description="Runtime verification for AI-built systems",
    )
    parser.add_argument("--version", action="version", version="wdog {}".format(__version__))

    sub = parser.add_subparsers(dest="command")

    # wdog check
    check_parser = sub.add_parser("check", help="Run all checks once")
    check_parser.add_argument("-c", "--config", help="Config file path")
    check_parser.add_argument("--json", action="store_true", help="JSON output")

    # wdog watch
    watch_parser = sub.add_parser("watch", help="Run checks on a schedule")
    watch_parser.add_argument("-c", "--config", help="Config file path")
    watch_parser.add_argument("--json", action="store_true", help="JSON output")

    # wdog init
    sub.add_parser("init", help="Generate example watchdog.yaml")

    # wdog list
    list_parser = sub.add_parser("list", help="List configured checks")
    list_parser.add_argument("-c", "--config", help="Config file path")

    args = parser.parse_args()

    if args.command == "init":
        _cmd_init()
    elif args.command == "check":
        _cmd_check(args)
    elif args.command == "watch":
        _cmd_watch(args)
    elif args.command == "list":
        _cmd_list(args)
    else:
        parser.print_help()
        sys.exit(0)


def _load(args):
    """Load config from args or auto-detect."""
    from wdog.config import load_config, find_config

    config_path = getattr(args, "config", None)
    if not config_path:
        config_path = find_config()
    if not config_path:
        print("Error: No watchdog.yaml found. Run 'wdog init' to create one.")
        sys.exit(1)

    try:
        return load_config(config_path)
    except Exception as e:
        print("Error loading config: {}".format(e))
        sys.exit(1)


def _cmd_init():
    """Generate example config."""
    from wdog.config import EXAMPLE_CONFIG

    target = "watchdog.yaml"
    if os.path.exists(target):
        print("Error: {} already exists".format(target))
        sys.exit(1)

    with open(target, "w") as f:
        f.write(EXAMPLE_CONFIG)

    print("Created {}".format(target))
    print("Edit it for your project, then run: wdog check")


def _cmd_check(args):
    """Run checks once."""
    from wdog.runner import run_checks

    config = _load(args)
    fmt = "json" if args.json else "terminal"
    exit_code = run_checks(config, fmt)
    sys.exit(exit_code)


def _cmd_watch(args):
    """Run checks on schedule."""
    from wdog.runner import run_daemon

    config = _load(args)
    fmt = "json" if args.json else "terminal"
    run_daemon(config, fmt)


def _cmd_list(args):
    """List configured checks."""
    config = _load(args)
    checks = config.get("checks", [])
    print("Configured checks ({}):\n".format(len(checks)))
    for i, c in enumerate(checks, 1):
        severity = c.get("severity", "warning")
        print("  {}. [{}] {} ({})".format(i, c["type"], c["name"], severity))


if __name__ == "__main__":
    main()
