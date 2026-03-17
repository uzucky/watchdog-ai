"""YAML config loader with environment variable interpolation."""

import os
import re

import yaml


DEFAULT_FILENAMES = ["watchdog.yaml", "watchdog.yml", ".watchdog.yaml", ".watchdog.yml"]


def find_config(start_dir=None):
    """Find watchdog config file in the given or current directory."""
    start_dir = start_dir or os.getcwd()
    for name in DEFAULT_FILENAMES:
        path = os.path.join(start_dir, name)
        if os.path.exists(path):
            return path
    return None


def load_config(path):
    """Load and validate a watchdog config file."""
    with open(path, "r") as f:
        raw = f.read()

    # Interpolate environment variables: ${VAR_NAME}
    raw = _interpolate_env(raw)

    config = yaml.safe_load(raw)
    if not config:
        raise ValueError("Empty config file: {}".format(path))

    config_dir = os.path.dirname(os.path.abspath(path))
    config["_config_dir"] = config_dir

    # Validate
    checks = config.get("checks", [])
    if not checks:
        raise ValueError("No checks defined in config")

    for i, check in enumerate(checks):
        if "name" not in check:
            raise ValueError("Check #{} missing 'name'".format(i + 1))
        if "type" not in check:
            raise ValueError("Check '{}' missing 'type'".format(check["name"]))
        # Inject config dir for relative path resolution
        check["_config_dir"] = config_dir

    return config


def _interpolate_env(text):
    """Replace ${VAR_NAME} with environment variable values."""
    def replacer(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            return match.group(0)  # leave as-is if not set
        return value
    return re.sub(r"\$\{(\w+)\}", replacer, text)


EXAMPLE_CONFIG = """# watchdog.yaml - Runtime verification for your AI-built systems
# Docs: https://github.com/uzucky/watchdog-ai

project: my-project
interval: 5m

checks:
  # Is your service running?
  - name: App server running
    type: process
    match: "python3 app.py"
    severity: critical

  # Is your data fresh?
  - name: Database updated recently
    type: freshness
    path: ./data/state.json
    max_age: 2h
    severity: warning

  # Any crashes in logs?
  - name: No crash loops
    type: log_scan
    path: ./logs/app.log
    patterns: ["traceback", "error", "killed"]
    tail: 50
    threshold: 3
    severity: critical

  # Is your data valid?
  - name: Balance is positive
    type: assertion
    source: ./data/state.json
    conditions:
      - expr: "$.balance > 0"
        message: "Balance went negative!"
        severity: critical

  # Is your API healthy?
  # - name: Health endpoint
  #   type: http
  #   url: http://localhost:8080/health
  #   expect_status: 200
  #   severity: critical

  # Custom validation script
  # - name: Custom check
  #   type: script
  #   command: "./scripts/validate.sh"

# Notifications (optional)
# notify:
#   - type: webhook
#     url: ${SLACK_WEBHOOK_URL}
#     on: [critical, warning]
"""
