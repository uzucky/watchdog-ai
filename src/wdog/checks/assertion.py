"""Assertion check - verify conditions on JSON data."""

import json
import os
import re

from wdog.checks.base import BaseCheck, CheckResult


class AssertionCheck(BaseCheck):
    """Check custom conditions on JSON data files.

    Config:
        source: str - path to JSON file
        conditions: list[dict] - conditions to evaluate
            - expr: str - expression like "$.capital > 500"
            - message: str - failure message (optional)
            - severity: str - override severity for this condition (optional)

    Expression syntax:
        $.path.to.field > 100
        $.path.to.field < $.other.field
        $.path.to.field == "value"
        $.path.to.field != null
        $.path.to.field contains "substring"
    """

    def run(self):
        source = self.config.get("source", "")
        conditions = self.config.get("conditions", [])

        source = os.path.expanduser(source)
        if not os.path.isabs(source):
            config_dir = self.config.get("_config_dir", ".")
            source = os.path.join(config_dir, source)

        if not os.path.exists(source):
            return self._fail("Source file not found: {}".format(source))

        try:
            with open(source, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return self._fail("Cannot read JSON: {}".format(e))

        failures = []
        for cond in conditions:
            expr = cond.get("expr", "")
            msg = cond.get("message", "")
            severity = cond.get("severity", self.severity)

            ok, err = _evaluate(expr, data)
            if not ok:
                failures.append({
                    "expr": expr,
                    "message": msg or err,
                    "severity": severity,
                })

        if not failures:
            return self._healthy(
                "All {} condition(s) passed".format(len(conditions)),
                {"conditions_checked": len(conditions)},
            )

        # Use worst severity from failures
        worst = "warning"
        for f in failures:
            if f["severity"] == "critical":
                worst = "critical"

        messages = [f["message"] or f["expr"] for f in failures]
        return CheckResult(
            name=self.name,
            status=worst,
            message="{} condition(s) failed: {}".format(
                len(failures), "; ".join(messages)),
            detail={"failures": failures, "total_conditions": len(conditions)},
        )


def _resolve(data, path):
    """Resolve $.path.to.field in data. Returns (value, found)."""
    if path == "null":
        return None, True
    if path.startswith("$."):
        path = path[2:]
    elif path.startswith("$"):
        path = path[1:]
    else:
        # Try as literal
        return _parse_literal(path)

    parts = path.split(".")
    current = data
    for part in parts:
        # Handle array index like items[0]
        m = re.match(r"^(\w+)\[(\d+)\]$", part)
        if m:
            key, idx = m.group(1), int(m.group(2))
            if isinstance(current, dict) and key in current:
                current = current[key]
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None, False
            else:
                return None, False
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None, False
    return current, True


def _parse_literal(s):
    """Parse a literal value from expression."""
    s = s.strip()
    if s == "null" or s == "None":
        return None, True
    if s == "true" or s == "True":
        return True, True
    if s == "false" or s == "False":
        return False, True
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1], True
    try:
        if "." in s:
            return float(s), True
        return int(s), True
    except ValueError:
        return s, False


def _evaluate(expr, data):
    """Evaluate an expression against data. Returns (ok, error_message)."""
    expr = expr.strip()

    # Parse: left op right
    operators = [
        (">=", lambda a, b: _num(a) >= _num(b)),
        ("<=", lambda a, b: _num(a) <= _num(b)),
        ("!=", lambda a, b: a != b),
        ("==", lambda a, b: a == b),
        (">", lambda a, b: _num(a) > _num(b)),
        ("<", lambda a, b: _num(a) < _num(b)),
        ("contains", lambda a, b: str(b) in str(a)),
    ]

    for op_str, op_fn in operators:
        # Split on operator (with word boundary for 'contains')
        if op_str == "contains":
            parts = re.split(r"\s+contains\s+", expr, maxsplit=1)
        else:
            parts = expr.split(op_str, 1)

        if len(parts) == 2:
            left_str = parts[0].strip()
            right_str = parts[1].strip()

            left_val, left_found = _resolve(data, left_str)
            if not left_found:
                return False, "Field not found: {}".format(left_str)

            right_val, right_found = _resolve(data, right_str)
            if not right_found:
                return False, "Field not found: {}".format(right_str)

            try:
                result = op_fn(left_val, right_val)
            except (TypeError, ValueError) as e:
                return False, "Comparison error: {} {} {} -> {}".format(
                    left_val, op_str, right_val, e)

            if result:
                return True, ""
            else:
                return False, "{} ({}) {} {} ({})".format(
                    left_str, left_val, op_str, right_str, right_val)

    return False, "Cannot parse expression: {}".format(expr)


def _num(v):
    """Convert to number for comparison."""
    if isinstance(v, (int, float)):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        raise TypeError("Cannot compare as number: {!r}".format(v))
