"""Base check class and result dataclass."""

from datetime import datetime


class CheckResult(object):
    """Result of a single check execution."""

    __slots__ = ("name", "status", "message", "detail", "timestamp")

    def __init__(self, name, status, message, detail=None, timestamp=None):
        self.name = name
        self.status = status  # "healthy", "warning", "critical"
        self.message = message
        self.detail = detail or {}
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return "CheckResult(name={!r}, status={!r}, message={!r})".format(
            self.name, self.status, self.message)


class BaseCheck(object):
    """Abstract base for all check types."""

    def __init__(self, config):
        self.name = config["name"]
        self.severity = config.get("severity", "warning")
        self.config = config

    def run(self):
        """Execute the check and return a CheckResult."""
        raise NotImplementedError

    def _result(self, status, message, detail=None):
        """Helper to create a CheckResult with this check's name."""
        return CheckResult(
            name=self.name,
            status=status,
            message=message,
            detail=detail,
        )

    def _healthy(self, message="OK", detail=None):
        return self._result("healthy", message, detail)

    def _fail(self, message, detail=None):
        return self._result(self.severity, message, detail)
