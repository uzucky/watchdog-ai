"""HTTP health check - verify endpoints return expected status."""

import json

from wdog.checks.base import BaseCheck
from wdog.checks.freshness import parse_duration

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import urlopen, Request, URLError, HTTPError


class HttpCheck(BaseCheck):
    """Check if an HTTP endpoint returns expected status.

    Config:
        url: str - URL to check
        expect_status: int - expected HTTP status code (default 200)
        timeout: str - timeout like "5s" (default "10s")
        method: str - HTTP method (default "GET")
        expect_body: str - optional string that must appear in response body
    """

    def run(self):
        url = self.config.get("url", "")
        expect_status = self.config.get("expect_status", 200)
        timeout_str = self.config.get("timeout", "10s")
        method = self.config.get("method", "GET")
        expect_body = self.config.get("expect_body")

        try:
            timeout_secs = parse_duration(timeout_str)
        except ValueError:
            timeout_secs = 10

        try:
            req = Request(url, method=method)
            resp = urlopen(req, timeout=timeout_secs)
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")[:10000]
        except HTTPError as e:
            status = e.code
            body = ""
        except URLError as e:
            return self._fail(
                "Connection failed: {}".format(e.reason),
                {"url": url},
            )
        except Exception as e:
            return self._fail(
                "Request error: {}".format(e),
                {"url": url},
            )

        detail = {"url": url, "status": status, "expected": expect_status}

        if status != expect_status:
            return self._fail(
                "Status {} (expected {})".format(status, expect_status),
                detail,
            )

        if expect_body and expect_body not in body:
            detail["expect_body"] = expect_body
            return self._fail(
                "Response missing expected content: '{}'".format(expect_body[:50]),
                detail,
            )

        return self._healthy(
            "Status {} OK".format(status),
            detail,
        )
