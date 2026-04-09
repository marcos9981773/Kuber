"""
kuber/services/monitoring_service.py
Application-level monitoring service with caching and aggregation.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from kuber.core.kubernetes.events import EventInfo, list_events
from kuber.core.kubernetes.logs import get_pod_logs, stream_pod_logs
from kuber.core.kubernetes.metrics import (
    NodeMetrics,
    PodMetrics,
    list_node_metrics,
    list_pod_metrics,
)

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 15


@dataclass
class MetricsSummary:
    """Aggregated metrics snapshot."""

    pod_count: int
    node_count: int
    total_pod_cpu_millicores: int
    total_pod_memory_mib: int
    total_node_cpu_millicores: int
    total_node_memory_mib: int
    avg_pod_cpu_millicores: float
    avg_pod_memory_mib: float


class MonitoringService:
    """
    Service layer for metrics, events, and logs.

    Provides:
    - Cached metrics fetching with configurable TTL
    - Aggregated summary helpers
    - Convenience wrappers for logs and events
    """

    def __init__(self, cache_ttl: int = _CACHE_TTL_SECONDS) -> None:
        self._cache_ttl = cache_ttl
        self._pod_metrics_cache: list[PodMetrics] = []
        self._node_metrics_cache: list[NodeMetrics] = []
        self._cache_ts: float = 0.0

    # ── Metrics ──────────────────────────────────────────────────────────────

    def get_pod_metrics(
        self, namespace: str = "default", force: bool = False
    ) -> list[PodMetrics]:
        """Return pod metrics, using cache if still fresh."""
        self._refresh_if_stale(namespace, force)
        return list(self._pod_metrics_cache)

    def get_node_metrics(self, force: bool = False) -> list[NodeMetrics]:
        """Return node metrics, using cache if still fresh."""
        self._refresh_if_stale("default", force)
        return list(self._node_metrics_cache)

    def get_all_metrics(
        self, namespace: str = "default", force: bool = False
    ) -> dict[str, Any]:
        """Return both pod and node metrics as a dict."""
        self._refresh_if_stale(namespace, force)
        return {
            "pods": list(self._pod_metrics_cache),
            "nodes": list(self._node_metrics_cache),
        }

    def get_summary(self, namespace: str = "default") -> MetricsSummary:
        """Return an aggregated metrics summary."""
        pods = self.get_pod_metrics(namespace)
        nodes = self.get_node_metrics()

        total_pod_cpu = sum(p.cpu_millicores for p in pods)
        total_pod_mem = sum(p.memory_mib for p in pods)
        total_node_cpu = sum(n.cpu_millicores for n in nodes)
        total_node_mem = sum(n.memory_mib for n in nodes)

        pod_count = len(pods)
        return MetricsSummary(
            pod_count=pod_count,
            node_count=len(nodes),
            total_pod_cpu_millicores=total_pod_cpu,
            total_pod_memory_mib=total_pod_mem,
            total_node_cpu_millicores=total_node_cpu,
            total_node_memory_mib=total_node_mem,
            avg_pod_cpu_millicores=total_pod_cpu / pod_count if pod_count else 0.0,
            avg_pod_memory_mib=total_pod_mem / pod_count if pod_count else 0.0,
        )

    # ── Events ───────────────────────────────────────────────────────────────

    def get_events(self, namespace: str = "default") -> list[EventInfo]:
        """Fetch cluster events for the given namespace."""
        return list_events(namespace=namespace)

    def get_warning_events(self, namespace: str = "default") -> list[EventInfo]:
        """Fetch only Warning-type events."""
        return [e for e in self.get_events(namespace) if e.type == "Warning"]

    # ── Logs ─────────────────────────────────────────────────────────────────

    def fetch_pod_logs(
        self,
        name: str,
        namespace: str = "default",
        container: str | None = None,
        tail_lines: int = 200,
    ) -> str:
        """Fetch pod logs (non-streaming)."""
        return get_pod_logs(
            name=name, namespace=namespace,
            container=container, tail_lines=tail_lines,
        )

    def stream_logs(
        self,
        name: str,
        namespace: str = "default",
        container: str | None = None,
        tail_lines: int = 50,
    ):
        """Return a generator that yields log lines."""
        return stream_pod_logs(
            name=name, namespace=namespace,
            container=container, tail_lines=tail_lines,
        )

    # ── Cache management ─────────────────────────────────────────────────────

    def invalidate_cache(self) -> None:
        """Force cache expiry so the next fetch hits the API."""
        self._cache_ts = 0.0

    def _refresh_if_stale(self, namespace: str, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._cache_ts) < self._cache_ttl:
            return
        try:
            self._pod_metrics_cache = list_pod_metrics(namespace=namespace)
            self._node_metrics_cache = list_node_metrics()
            self._cache_ts = now
            logger.debug("Metrics cache refreshed for namespace '%s'.", namespace)
        except Exception as exc:
            logger.warning("Failed to refresh metrics cache: %s", exc)
            raise

