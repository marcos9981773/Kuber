"""
kuber/core/helm/client.py
Helm chart operations via subprocess.
No PyQt5 imports.
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from kuber.core.exceptions import KuberHelmError

logger = logging.getLogger(__name__)

_HELM_TIMEOUT = "300s"


@dataclass
class HelmRelease:
    """Represents an installed Helm release."""

    name: str
    namespace: str
    chart: str
    chart_version: str
    app_version: str
    status: str
    updated: str


@dataclass
class HelmChartInfo:
    """Metadata for a chart from a Helm repository."""

    name: str
    version: str
    app_version: str
    description: str


def _run_helm(*args: str, timeout: int = 60) -> str:
    """
    Execute a helm command and return its stdout.

    Raises:
        KuberHelmError: If helm is not found or the command fails.
    """
    cmd = ["helm", *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise KuberHelmError(
            "Helm is not installed or not found in PATH.",
            details="Install Helm from https://helm.sh/docs/intro/install/",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise KuberHelmError(
            f"Helm command timed out after {timeout}s.",
            details=" ".join(cmd),
        ) from exc

    if result.returncode != 0:
        raise KuberHelmError(
            f"Helm command failed: {' '.join(cmd)}",
            details=result.stderr.strip(),
        )
    return result.stdout


def list_releases(namespace: str = "default") -> list[HelmRelease]:
    """
    List all Helm releases in a namespace.

    Args:
        namespace: Target namespace (``"all"`` lists across all namespaces).

    Returns:
        List of :class:`HelmRelease` objects.
    """
    args = ["list", "--output", "json"]
    if namespace == "all":
        args.append("--all-namespaces")
    else:
        args.extend(["-n", namespace])

    output = _run_helm(*args)
    try:
        raw: list[dict] = json.loads(output) if output.strip() else []  # type: ignore[type-arg]
    except json.JSONDecodeError as exc:
        raise KuberHelmError("Failed to parse helm list output.", details=str(exc)) from exc

    return [
        HelmRelease(
            name=r.get("name", ""),
            namespace=r.get("namespace", ""),
            chart=r.get("chart", ""),
            chart_version=r.get("chart", "").split("-")[-1] if "-" in r.get("chart", "") else "",
            app_version=r.get("app_version", ""),
            status=r.get("status", ""),
            updated=r.get("updated", ""),
        )
        for r in raw
    ]


def install_chart(
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: dict | None = None,  # type: ignore[type-arg]
    values_file: Path | None = None,
    dry_run: bool = False,
    timeout: int = 300,
) -> str:
    """
    Install a Helm chart.

    Args:
        release_name: Name for the Helm release.
        chart:        Chart reference (``"repo/chart"`` or path).
        namespace:    Target namespace.
        values:       Inline values dict (passed via ``--set``).
        values_file:  Path to a values YAML file (passed via ``-f``).
        dry_run:      If True, perform a dry-run only.
        timeout:      Helm operation timeout in seconds.

    Returns:
        Helm command stdout output.
    """
    args = [
        "install", release_name, chart,
        "-n", namespace,
        "--create-namespace",
        "--timeout", f"{timeout}s",
        "--output", "json",
    ]
    if dry_run:
        args.append("--dry-run")
    if values_file:
        args.extend(["-f", str(values_file)])
    if values:
        for key, val in values.items():
            args.extend(["--set", f"{key}={val}"])

    logger.info(f"Installing Helm chart '{chart}' as '{release_name}' in '{namespace}'.")
    return _run_helm(*args, timeout=timeout + 30)


def uninstall_release(
    release_name: str,
    namespace: str = "default",
    timeout: int = 120,
) -> None:
    """Uninstall a Helm release."""
    logger.info(f"Uninstalling Helm release '{release_name}' from '{namespace}'.")
    _run_helm("uninstall", release_name, "-n", namespace, "--timeout", f"{timeout}s",
              timeout=timeout + 30)


def upgrade_chart(
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: dict | None = None,  # type: ignore[type-arg]
    values_file: Path | None = None,
    timeout: int = 300,
) -> str:
    """Upgrade an existing Helm release."""
    args = [
        "upgrade", release_name, chart,
        "-n", namespace,
        "--timeout", f"{timeout}s",
        "--output", "json",
    ]
    if values_file:
        args.extend(["-f", str(values_file)])
    if values:
        for key, val in (values or {}).items():
            args.extend(["--set", f"{key}={val}"])

    logger.info(f"Upgrading Helm release '{release_name}' with chart '{chart}'.")
    return _run_helm(*args, timeout=timeout + 30)

