# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Helper functions for discovering ELF files and configuration files.

This module provides utilities for:
- Finding ELF files recursively in directories
- Resolving ELF paths from various sources (direct paths, file:// URIs, environment variables)
- Locating memtab configuration files
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List
from urllib.parse import unquote, urlparse


def get_default_search_depth() -> int:
    """Get the default recursive search depth for MCP ELF discovery.

    Uses MEMTAB_MCP_DEFAULT_SEARCH_DEPTH if set to a non-negative integer,
    otherwise defaults to 4 to avoid expensive unbounded scans.

    :return: Default maximum search depth.
    """
    configured_depth = os.environ.get("MEMTAB_MCP_DEFAULT_SEARCH_DEPTH")
    if configured_depth and configured_depth.isdigit():
        return int(configured_depth)
    return 4


def get_allowed_roots() -> List[Path]:
    """Get the allowlisted filesystem roots for MCP file access.

    Uses MEMTAB_ALLOWED_ROOTS (path-separated) when set. Otherwise, defaults
    to the current working directory.

    :return: List of resolved allowed root directories.
    """
    configured_roots = os.environ.get("MEMTAB_ALLOWED_ROOTS")
    if configured_roots:
        roots = [Path(root).resolve() for root in configured_roots.split(os.pathsep) if root.strip()]
        if roots:
            return roots
    return [Path(os.getcwd()).resolve()]


def is_within_allowed_roots(path: Path, allowed_roots: List[Path] | None = None) -> bool:
    """Check whether a path resolves under any allowlisted root.

    :param path: Path to validate.
    :param allowed_roots: Optional explicit allowed roots.
    :return: True when the path is under an allowed root.
    """
    roots = allowed_roots if allowed_roots is not None else get_allowed_roots()
    resolved_path = path.resolve()

    for root in roots:
        resolved_root = root.resolve()
        if resolved_path == resolved_root or resolved_path.is_relative_to(resolved_root):
            return True
    return False


def find_elf_files(start_dir: str | None = None, max_depth: int | None = None, allowed_roots: List[Path] | None = None) -> List[str]:
    """Recursively find all .elf files in the specified directory.

    :param start_dir: Directory to start search from. Defaults to current working directory.
    :param max_depth: Maximum depth to search. Defaults to a bounded MCP-safe value.
    :param allowed_roots: Optional list of roots to constrain discovered paths.
    :return: List of absolute paths to .elf files.
    """
    if start_dir is None:
        start_dir = os.getcwd()

    if max_depth is None:
        max_depth_str = os.environ.get("MEMTAB_SEARCH_DEPTH")
        if max_depth_str and max_depth_str.isdigit():
            max_depth = int(max_depth_str)
        else:
            max_depth = get_default_search_depth()

    elf_files = []
    start_path = Path(start_dir).resolve()
    roots = allowed_roots if allowed_roots is not None else get_allowed_roots()

    if not is_within_allowed_roots(start_path, roots):
        return []

    def _search(path: Path, current_depth: int) -> None:
        """Recursively search for .elf files."""
        if max_depth is not None and current_depth > max_depth:
            return

        try:
            for item in path.iterdir():
                if item.is_file() and item.suffix == ".elf" and is_within_allowed_roots(item, roots):
                    elf_files.append(str(item.absolute()))
                elif item.is_dir() and is_within_allowed_roots(item, roots):
                    _search(item, current_depth + 1)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

    _search(start_path, 0)
    return sorted(elf_files)


def resolve_elf_path(elf: str | None) -> str:
    """Resolve an ELF file path from various sources.

    Accepts:
    - Direct file path
    - file:// URI
    - None (will search for MEMTAB_ELF env var or auto-discover)

    :param elf: ELF file path, URI, or None.
    :return: Absolute path to the ELF file.
    :raises ValueError: If no ELF file can be found.
    """
    # If elf is provided, check if it's a URI
    if elf:
        if elf.startswith("file://"):
            # Extract path from file:// URI
            parsed = urlparse(elf)
            elf = unquote(parsed.path)
            # Handle Windows paths that might have a leading slash
            if os.name == "nt" and elf.startswith("/") and ":" in elf:
                elf = elf[1:]
            return os.path.abspath(elf)
        else:
            # It's a regular path
            return os.path.abspath(elf)

    # Try environment variable
    elf = os.environ.get("MEMTAB_ELF")
    if elf:
        return os.path.abspath(elf)

    # Try to find a .elf file in the current directory (non-recursive for backward compatibility)
    for fname in os.listdir(os.getcwd()):
        if fname.endswith(".elf"):
            return os.path.abspath(fname)

    raise ValueError("No ELF file specified and none found in the current directory.")


def search_for_config_in_directory(directory: str, patterns: List[str]) -> str | None:
    """Search for config files matching given patterns in a directory.

    :param directory: Directory to search in.
    :param patterns: List of file ending patterns to match.
    :return: Absolute path to first matching file, or None if not found.
    """
    try:
        for fname in os.listdir(directory):
            for pattern in patterns:
                if fname.endswith(pattern):
                    return os.path.abspath(os.path.join(directory, fname))
    except (OSError, PermissionError):
        pass
    return None


def get_config_file(elf_path: str) -> str:
    """Find the memtab configuration file.

    Search order:
    1. MEMTAB_CONFIG environment variable
    2. memtab.yml or memtab.yaml in current directory
    3. memtab.yml or memtab.yaml in ELF's directory

    :param elf_path: Path to the ELF file.
    :return: Absolute path to config file.
    :raises ValueError: If no config file is found.
    """
    config = os.environ.get("MEMTAB_CONFIG")
    if config:
        return os.path.abspath(config)

    # Search for memtab config in current directory
    config = search_for_config_in_directory(os.getcwd(), ["memtab.yml", "memtab.yaml"])
    if config:
        return config

    # Search in ELF's directory
    elf_dir = os.path.dirname(elf_path)
    config = search_for_config_in_directory(elf_dir, ["memtab.yml", "memtab.yaml"])
    if config:
        return config

    raise ValueError("No configuration file specified and none found in the current directory or in the ELF's directory.")
