"""
kuber/core/docker/client.py
Docker daemon interaction — version check, status, image pull.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import docker
from docker.errors import DockerException, ImageNotFound, NotFound

from kuber.constants import HTTP_TIMEOUT_SECONDS, MIN_DOCKER_VERSION
from kuber.core.exceptions import (
    KuberDockerError,
    KuberDockerNotRunningError,
    KuberDockerVersionError,
)

logger = logging.getLogger(__name__)


@dataclass
class DockerStatus:
    """Result of a Docker health check."""

    is_running: bool
    version: str
    version_ok: bool
    server_os: str = ""
    server_arch: str = ""


def get_docker_client() -> docker.DockerClient:
    """
    Return a connected Docker client.

    Raises:
        KuberDockerNotRunningError: If the Docker daemon is not running.
    """
    try:
        client = docker.from_env(timeout=HTTP_TIMEOUT_SECONDS)
        client.ping()
        return client
    except DockerException as exc:
        raise KuberDockerNotRunningError(
            "Docker daemon is not running.",
            details=(
                "Start the Docker Desktop application or run 'dockerd' and try again."
            ),
        ) from exc


def check_docker_status() -> DockerStatus:
    """
    Check whether Docker is running and meets the minimum version requirement.

    Returns:
        :class:`DockerStatus` with connectivity and version information.
    """
    try:
        client = get_docker_client()
        info = client.version()
        version_str: str = info.get("Version", "0.0.0")
        version_parts = tuple(
            int(x) for x in version_str.split(".")[:3] if x.isdigit()
        )
        version_ok = version_parts >= MIN_DOCKER_VERSION
        components = info.get("Components", [{}])
        engine_info = next(
            (c for c in components if c.get("Name", "").lower() == "engine"), {}
        )
        details = engine_info.get("Details", {})

        return DockerStatus(
            is_running=True,
            version=version_str,
            version_ok=version_ok,
            server_os=details.get("Os", ""),
            server_arch=details.get("Arch", ""),
        )
    except KuberDockerNotRunningError:
        return DockerStatus(is_running=False, version="", version_ok=False)


def pull_image(
    image: str,
    tag: str = "latest",
    timeout: int = 300,
) -> None:
    """
    Pull a Docker image from a registry.

    Args:
        image:   Image name (e.g., ``"nginx"``).
        tag:     Image tag (default: ``"latest"``).
        timeout: Pull timeout in seconds.

    Raises:
        KuberDockerNotRunningError: If the Docker daemon is unavailable.
        KuberDockerError:           On pull failure.
    """
    client = get_docker_client()
    image_ref = f"{image}:{tag}"
    try:
        logger.info(f"Pulling image '{image_ref}'…")
        client.images.pull(image, tag=tag)
        logger.info(f"Image '{image_ref}' pulled successfully.")
    except DockerException as exc:
        raise KuberDockerError(
            f"Failed to pull image '{image_ref}'.",
            details=str(exc),
        ) from exc


def list_local_images() -> list[str]:
    """
    Return a list of locally available Docker image tags.

    Raises:
        KuberDockerNotRunningError: If the Docker daemon is unavailable.
    """
    client = get_docker_client()
    tags: list[str] = []
    for img in client.images.list():
        for tag in img.tags:
            tags.append(tag)
    return sorted(tags)

