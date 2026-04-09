"""
kuber/core/git/client.py
Git configuration validation and repository access checks.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

import git
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from kuber.constants import MIN_GIT_VERSION
from kuber.core.exceptions import (
    KuberGitAccessError,
    KuberGitConfigError,
    KuberGitError,
)

logger = logging.getLogger(__name__)


@dataclass
class GitStatus:
    """Result of a Git environment check."""

    is_installed: bool
    version: str
    version_ok: bool
    user_name: str = ""
    user_email: str = ""
    config_ok: bool = False


def check_git_status() -> GitStatus:
    """
    Check Git installation, version, and global configuration.

    Returns:
        :class:`GitStatus` with environment information.
    """
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return GitStatus(is_installed=False, version="", version_ok=False)

        # Parse "git version x.y.z"
        version_str = result.stdout.strip().split()[-1]
        parts = tuple(int(x) for x in version_str.split(".")[:3] if x.isdigit())
        version_ok = parts >= MIN_GIT_VERSION

        # Read global config
        user_name = _git_config("user.name")
        user_email = _git_config("user.email")
        config_ok = bool(user_name and user_email)

        return GitStatus(
            is_installed=True,
            version=version_str,
            version_ok=version_ok,
            user_name=user_name,
            user_email=user_email,
            config_ok=config_ok,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return GitStatus(is_installed=False, version="", version_ok=False)


def validate_git_config() -> None:
    """
    Ensure Git is installed, meets the version requirement, and has a valid config.

    Raises:
        KuberGitConfigError: If Git is missing, outdated, or has no user config.
    """
    status = check_git_status()
    if not status.is_installed:
        raise KuberGitConfigError(
            "Git is not installed.",
            details="Install Git 2.39+ from https://git-scm.com/",
        )
    if not status.version_ok:
        min_str = ".".join(str(v) for v in MIN_GIT_VERSION)
        raise KuberGitConfigError(
            f"Git version {status.version} is below the minimum required {min_str}.",
            details=f"Upgrade Git to version {min_str} or later.",
        )
    if not status.config_ok:
        raise KuberGitConfigError(
            "Git user.name or user.email is not configured.",
            details=(
                "Run: git config --global user.name 'Your Name' && "
                "git config --global user.email 'you@example.com'"
            ),
        )


def check_repo_access(repo_url: str, timeout: int = 30) -> None:
    """
    Verify that the current Git credentials can access a remote repository.

    Performs a ``git ls-remote`` without cloning.

    Args:
        repo_url: Remote URL (SSH or HTTPS).
        timeout:  Operation timeout in seconds.

    Raises:
        KuberGitAccessError: If the repository cannot be accessed.
    """
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", repo_url],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise KuberGitAccessError(
                f"Cannot access repository '{repo_url}'.",
                details=result.stderr.strip(),
            )
        logger.debug(f"Repository '{repo_url}' is accessible.")
    except subprocess.TimeoutExpired as exc:
        raise KuberGitAccessError(
            f"Timed out while checking access to '{repo_url}'.",
        ) from exc
    except FileNotFoundError as exc:
        raise KuberGitConfigError(
            "Git is not installed.",
            details="Install Git and try again.",
        ) from exc


def clone_repository(
    repo_url: str,
    destination: Path,
    branch: str = "main",
    depth: int = 1,
) -> git.Repo:
    """
    Shallow-clone a repository to ``destination``.

    Args:
        repo_url:    Remote URL.
        destination: Local path to clone into.
        branch:      Branch to clone.
        depth:       Shallow clone depth.

    Returns:
        A :class:`git.Repo` instance.

    Raises:
        KuberGitAccessError: If the clone fails.
    """
    try:
        logger.info(f"Cloning '{repo_url}' → '{destination}' (branch={branch})…")
        repo = git.Repo.clone_from(
            repo_url,
            str(destination),
            branch=branch,
            depth=depth,
        )
        return repo
    except GitCommandError as exc:
        raise KuberGitAccessError(
            f"Failed to clone repository '{repo_url}'.",
            details=str(exc),
        ) from exc


# ── Private helpers ──────────────────────────────────────────────────────────

def _git_config(key: str) -> str:
    """Read a single git config value; return empty string if not set."""
    try:
        result = subprocess.run(
            ["git", "config", "--global", key],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip()
    except Exception:
        return ""

