"""
tests/unit/core/kubernetes/test_client.py
Tests for kuber/core/kubernetes/client.py
"""
from __future__ import annotations

import pytest
from kubernetes.client.exceptions import ApiException

from kuber.core.exceptions import (
    KuberApiError,
    KuberConnectionError,
    KuberNotFoundError,
    KuberPermissionError,
)
from kuber.core.kubernetes.client import call_with_retry


class TestCallWithRetry:
    """Tests for the call_with_retry helper."""

    def test_call_with_retry_success_returns_value(self) -> None:
        """Successful call returns the function's return value."""
        result = call_with_retry(lambda: 42)
        assert result == 42

    def test_call_with_retry_403_raises_permission_error(self) -> None:
        """HTTP 403 is immediately raised as KuberPermissionError (no retry)."""
        def _raise() -> None:
            raise ApiException(status=403, reason="Forbidden")

        with pytest.raises(KuberPermissionError):
            call_with_retry(_raise, max_attempts=3)

    def test_call_with_retry_404_raises_not_found_error(self) -> None:
        """HTTP 404 is immediately raised as KuberNotFoundError (no retry)."""
        def _raise() -> None:
            raise ApiException(status=404, reason="Not Found")

        with pytest.raises(KuberNotFoundError):
            call_with_retry(_raise, max_attempts=3)

    def test_call_with_retry_500_retries_and_raises_connection_error(
        self, mocker
    ) -> None:
        """HTTP 500 is retried and eventually raises KuberConnectionError."""
        mocker.patch("time.sleep")  # speed up test
        call_count = 0

        def _raise() -> None:
            nonlocal call_count
            call_count += 1
            raise ApiException(status=500, reason="Internal Server Error")

        with pytest.raises(KuberConnectionError):
            call_with_retry(_raise, max_attempts=3, base_delay=0.01)

        assert call_count == 3

    def test_call_with_retry_generic_exception_retries(self, mocker) -> None:
        """Generic exceptions are retried up to max_attempts."""
        mocker.patch("time.sleep")
        attempts = []

        def _flaky() -> str:
            attempts.append(1)
            if len(attempts) < 3:
                raise ConnectionError("transient")
            return "ok"

        result = call_with_retry(_flaky, max_attempts=3, base_delay=0.01)
        assert result == "ok"
        assert len(attempts) == 3

