"""
kuber/core/kubernetes/client.py
Low-level Kubernetes API client wrapper with retry and timeout logic.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, TypeVar

from kubernetes import client as k8s_client
from kubernetes.client.exceptions import ApiException

from kuber.constants import (
    K8S_API_TIMEOUT_SECONDS,
    RETRY_BASE_DELAY_SECONDS,
    RETRY_BACKOFF_MULTIPLIER,
    RETRY_MAX_ATTEMPTS,
)
from kuber.core.exceptions import (
    KuberApiError,
    KuberConnectionError,
    KuberNotFoundError,
    KuberPermissionError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ── Transient HTTP status codes that warrant a retry ────────────────────────
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def call_with_retry(
    fn: Callable[..., T],
    *args: Any,
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY_SECONDS,
    backoff: float = RETRY_BACKOFF_MULTIPLIER,
    **kwargs: Any,
) -> T:
    """
    Execute a callable with exponential back-off retry logic.

    Re-raises on non-retryable errors (403, 404, etc.) immediately.
    Retries on transient failures (5xx, 429, connection errors) up to
    ``max_attempts`` times.

    Args:
        fn:           The callable to invoke.
        *args:        Positional arguments forwarded to ``fn``.
        max_attempts: Maximum number of attempts.
        base_delay:   Seconds to wait before the first retry.
        backoff:      Multiplier applied to the delay after each retry.
        **kwargs:     Keyword arguments forwarded to ``fn``.

    Returns:
        The return value of ``fn``.

    Raises:
        KuberPermissionError: On HTTP 403.
        KuberNotFoundError:   On HTTP 404.
        KuberApiError:        On non-retryable API errors.
        KuberConnectionError: When the API server is unreachable after all retries.
    """
    delay = base_delay
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except ApiException as exc:
            last_exc = exc
            _raise_for_status(exc)                        # raises for 403, 404, …
            if exc.status not in _RETRYABLE_STATUSES:
                raise KuberApiError(
                    f"Kubernetes API error (status {exc.status}).",
                    status_code=exc.status,
                    details=exc.reason or "",
                ) from exc
            logger.warning(
                f"Kubernetes API transient error {exc.status} "
                f"(attempt {attempt}/{max_attempts}). Retrying in {delay:.1f}s…"
            )
        except Exception as exc:
            last_exc = exc
            logger.warning(
                f"Kubernetes call failed (attempt {attempt}/{max_attempts}): {exc}. "
                f"Retrying in {delay:.1f}s…"
            )

        if attempt < max_attempts:
            time.sleep(delay)
            delay *= backoff

    raise KuberConnectionError(
        "Could not reach the Kubernetes API server after multiple attempts.",
        details=str(last_exc),
    ) from last_exc


def _raise_for_status(exc: ApiException) -> None:
    """Convert well-known ApiException status codes to domain exceptions."""
    if exc.status == 403:
        raise KuberPermissionError(
            "Insufficient permissions to perform this operation.",
            details=exc.reason or "",
        ) from exc
    if exc.status == 404:
        raise KuberNotFoundError(
            "The requested Kubernetes resource was not found.",
            details=exc.reason or "",
        ) from exc


# ── Typed API accessor helpers ───────────────────────────────────────────────

def core_v1() -> k8s_client.CoreV1Api:
    """Return a CoreV1Api client instance."""
    return k8s_client.CoreV1Api()


def apps_v1() -> k8s_client.AppsV1Api:
    """Return an AppsV1Api client instance."""
    return k8s_client.AppsV1Api()


def rbac_v1() -> k8s_client.RbacAuthorizationV1Api:
    """Return an RbacAuthorizationV1Api client instance."""
    return k8s_client.RbacAuthorizationV1Api()


def custom_objects() -> k8s_client.CustomObjectsApi:
    """Return a CustomObjectsApi client instance."""
    return k8s_client.CustomObjectsApi()


def version_api() -> k8s_client.VersionApi:
    """Return a VersionApi client instance."""
    return k8s_client.VersionApi()

