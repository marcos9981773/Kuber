"""
kuber/core/kubernetes/logs.py
Pod log streaming via Kubernetes API.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from typing import Generator

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.kubernetes.client import call_with_retry, core_v1

logger = logging.getLogger(__name__)


def get_pod_logs(
    name: str,
    namespace: str = "default",
    container: str | None = None,
    tail_lines: int = 100,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> str:
    """
    Fetch the last ``tail_lines`` of logs for a pod.

    Returns:
        The log text as a single string.
    """
    def _call() -> str:
        kwargs: dict = {
            "name": name,
            "namespace": namespace,
            "tail_lines": tail_lines,
            "_request_timeout": timeout,
        }
        if container:
            kwargs["container"] = container
        return core_v1().read_namespaced_pod_log(**kwargs)

    return call_with_retry(_call)


def stream_pod_logs(
    name: str,
    namespace: str = "default",
    container: str | None = None,
    tail_lines: int = 50,
    timeout: int = 300,
) -> Generator[str, None, None]:
    """
    Stream live pod logs line-by-line.

    Yields:
        Individual log lines as they arrive.
    """
    kwargs: dict = {
        "name": name,
        "namespace": namespace,
        "follow": True,
        "tail_lines": tail_lines,
        "_preload_content": False,
        "_request_timeout": timeout,
    }
    if container:
        kwargs["container"] = container

    api = core_v1()
    resp = api.read_namespaced_pod_log(**kwargs)
    try:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
            yield line
    finally:
        resp.close()

