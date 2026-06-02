# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""The main MCP server for memtab.

This module provides the FastMCP server implementation that exposes memtab
functionality through the Model Context Protocol. It includes:

- Tools for analyzing memory usage and creating configurations
- Resources for discovering and accessing ELF files
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import unquote, urlparse

import yaml
from fastmcp import FastMCP

from memtab.mcp.discovery import (
    find_elf_files,
    get_allowed_roots,
    get_config_file,
    get_default_search_depth,
    is_within_allowed_roots,
    resolve_elf_path,
)
from memtab.memtab import Memtab

mcp = FastMCP("Memory Tabulator MCP Server")
logger = logging.getLogger(__name__)


def _get_max_elf_bytes() -> int:
    """Get the maximum ELF size allowed for MCP analysis.

    Uses MEMTAB_MAX_ELF_BYTES when set to a positive integer,
    otherwise defaults to 500 MB.

    :return: Maximum allowed ELF file size in bytes.
    """
    configured_limit = os.environ.get("MEMTAB_MAX_ELF_BYTES")
    if configured_limit and configured_limit.isdigit():
        max_bytes = int(configured_limit)
        if max_bytes > 0:
            return max_bytes
    return 500 * 1024 * 1024


def _normalize_input_path(path_or_uri: str) -> Path:
    """Normalize file input that may be a local path or file:// URI.

    :param path_or_uri: File path input from MCP resource/tool.
    :return: Normalized filesystem path.
    """
    if path_or_uri.startswith("file://"):
        parsed = urlparse(path_or_uri)
        file_path = unquote(parsed.path)
        if os.name == "nt" and file_path.startswith("/") and ":" in file_path:
            file_path = file_path[1:]
        return Path(file_path).resolve()
    return Path(path_or_uri).resolve()


def _enforce_allowed_file_access(path_or_uri: str, *, expected_suffixes: tuple[str, ...] | None = None) -> Path:
    """Validate that a path is inside allowlisted roots.

    :param path_or_uri: File path or file:// URI.
    :param expected_suffixes: Optional allowed file suffixes.
    :return: Validated and resolved path.
    :raises PermissionError: If the path is outside allowed roots.
    :raises ValueError: If file extension does not match expected suffixes.
    """
    path_obj = _normalize_input_path(path_or_uri)
    allowed_roots = get_allowed_roots()

    if not is_within_allowed_roots(path_obj, allowed_roots):
        allowed_display = ", ".join(str(root) for root in allowed_roots)
        raise PermissionError(f"Path '{path_obj}' is outside allowed roots: {allowed_display}")

    if expected_suffixes and path_obj.suffix.lower() not in expected_suffixes:
        allowed_suffixes = ", ".join(expected_suffixes)
        raise ValueError(f"Invalid file type '{path_obj.suffix}'. Allowed suffixes: {allowed_suffixes}")

    return path_obj


def _enforce_elf_size_limit(elf_path: Path) -> None:
    """Validate ELF file size before analysis.

    :param elf_path: Path to the ELF file.
    :raises ValueError: If ELF file exceeds allowed size.
    """
    max_bytes = _get_max_elf_bytes()
    elf_size = elf_path.stat().st_size
    if elf_size > max_bytes:
        raise ValueError(f"ELF file '{elf_path}' is too large ({elf_size} bytes). Maximum allowed size is {max_bytes} bytes.")


@mcp.resource("elf://files")
def list_elf_files() -> List[Dict[str, Any]]:
    """List all available ELF files as MCP resources.

    Returns a list of ELF files found in the workspace with metadata and annotations
    to help clients understand their purpose and priority for memory analysis.
    """
    elf_files = find_elf_files(
        start_dir=os.getcwd(),
        max_depth=get_default_search_depth(),
        allowed_roots=get_allowed_roots(),
    )
    resources = []

    for elf_path in elf_files:
        path_obj = Path(elf_path)
        stat = path_obj.stat()

        # Create file:// URI
        file_uri = path_obj.as_uri()

        resources.append(
            {
                "uri": file_uri,
                "name": path_obj.name,
                "description": f"ELF executable file for memory analysis ({stat.st_size} bytes)",
                "mimeType": "application/x-executable",
                "annotations": {
                    "audience": ["assistant"],
                    "priority": 0.9,
                },
            }
        )

    return resources


@mcp.resource("elf://file/{path}")
def read_elf_file(path: str) -> str:
    """Read ELF file metadata.

    Returns metadata about the ELF file including size and modification time,
    but not the binary content itself (which would be large and unnecessary).

    :param path: The path to the ELF file (can be a file:// URI or regular path).
    :return: Formatted metadata string.
    :raises FileNotFoundError: If the ELF file doesn't exist.
    """
    path_obj = _enforce_allowed_file_access(path, expected_suffixes=(".elf",))

    if not path_obj.exists():
        raise FileNotFoundError(f"ELF file not found: {path_obj}")

    _enforce_elf_size_limit(path_obj)

    stat = path_obj.stat()

    # Return metadata as a formatted string
    metadata = f"""ELF File: {path_obj.name}
Path: {path_obj.absolute()}
Size: {stat.st_size} bytes ({stat.st_size / 1024:.2f} KB)
Last Modified: {stat.st_mtime}

This is an ELF (Executable and Linkable Format) binary file used for memory analysis.
Use the get_memory_table tool to analyze its memory usage."""

    return metadata


def _get_memory_table(elf: str | None) -> List[Dict[str, Any]]:
    """Internal implementation of memory table generation.

    Returns a list containing the top 10 largest symbols by size. Each entry
    includes symbol metadata such as size and location.

    :param elf: Path to ELF file, file:// URI, or None to auto-discover.
    :return: List of top-10 symbol dictionaries sorted by descending size.
    """
    resolved_elf = resolve_elf_path(elf)
    elf_path = _enforce_allowed_file_access(resolved_elf, expected_suffixes=(".elf",))
    if not elf_path.exists():
        raise FileNotFoundError(f"ELF file not found: {elf_path}")
    _enforce_elf_size_limit(elf_path)

    config = get_config_file(str(elf_path))
    config_path = _enforce_allowed_file_access(config, expected_suffixes=(".yml", ".yaml"))
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    logger.info("Using configuration file: %s", config_path)
    logger.info("Using ELF file: %s", elf_path)

    tabulator = Memtab(elf=elf_path, config=[config_path], cache=True)
    tabulator.tabulate()
    logger.info("Tabulation complete.")

    return_dict = tabulator.memtab

    # Find the top 10 symbols by size
    top_symbols = sorted(return_dict["symbols"], key=lambda x: x.get("size", 0), reverse=True)[:10]

    return top_symbols


@mcp.tool()
def get_memory_table(elf: str | None) -> List[Dict[str, Any]]:
    """Runs the memory tabulator on the given ELF file and configuration file.

    Returns the top 10 largest symbols by size from the analyzed ELF.

    :param elf: Path to ELF file, file:// URI, or None to auto-discover.
    :return: List of top-10 symbol dictionaries sorted by descending size.
    """
    return _get_memory_table(elf)


@mcp.tool()
def create_memtab_config(elf: str | None) -> str:
    """Generates a memtab configuration YML file content.

    :param elf: Path to ELF file, file:// URI, or None to auto-discover.
    :return: YAML configuration content as a string.
    """
    resolved_elf = resolve_elf_path(elf)
    elf_path = _enforce_allowed_file_access(resolved_elf, expected_suffixes=(".elf",))
    if not elf_path.exists():
        raise FileNotFoundError(f"ELF file not found: {elf_path}")
    _enforce_elf_size_limit(elf_path)

    # Create a Memtab instance to extract memory information from the ELF
    # This will auto-generate default config if none exists
    tabulator = Memtab(elf=elf_path, config=[], cache=True)

    # Get the configuration as a dictionary
    config_dict = tabulator.config.asdict()

    logger.info("Generated configuration based on ELF file: %s", elf_path)

    # Convert the configuration to YAML string
    yaml_content = yaml.safe_dump(config_dict, default_flow_style=False, sort_keys=False)

    return yaml_content
