"""
tests/unit/core/kubernetes/test_metrics.py
Tests for kuber/core/kubernetes/metrics.py
"""
from __future__ import annotations

from kuber.core.kubernetes.metrics import _parse_cpu, _parse_memory


class TestParseCpu:
    def test_millicores(self) -> None:
        assert _parse_cpu("250m") == 250

    def test_whole_cores(self) -> None:
        assert _parse_cpu("2") == 2000

    def test_nanocores(self) -> None:
        assert _parse_cpu("500000000n") == 500

    def test_microcores(self) -> None:
        assert _parse_cpu("500000u") == 500


class TestParseMemory:
    def test_mebibytes(self) -> None:
        assert _parse_memory("128Mi") == 128

    def test_gibibytes(self) -> None:
        assert _parse_memory("2Gi") == 2048

    def test_kibibytes(self) -> None:
        assert _parse_memory("1024Ki") == 1

    def test_plain_bytes(self) -> None:
        assert _parse_memory("1048576") == 1

