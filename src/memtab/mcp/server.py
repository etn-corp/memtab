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
    get_config_file,
    resolve_elf_path,
)
from memtab.memtab import Memtab

mcp = FastMCP("Memory Tabulator MCP Server")
logger = logging.getLogger(__name__)


@mcp.resource("elf://files")
def list_elf_files() -> List[Dict[str, Any]]:
    """List all available ELF files as MCP resources.

    Returns a list of ELF files found in the workspace with metadata and annotations
    to help clients understand their purpose and priority for memory analysis.
    """
    elf_files = find_elf_files()
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
    # Extract path from URI if needed
    if path.startswith("file://"):
        parsed = urlparse(path)
        file_path = unquote(parsed.path)
        # Handle Windows paths
        if os.name == "nt" and file_path.startswith("/") and ":" in file_path:
            file_path = file_path[1:]
    else:
        file_path = path

    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"ELF file not found: {file_path}")

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
    elf = resolve_elf_path(elf)
    config = get_config_file(elf)

    logger.info("Using configuration file: %s", config)
    logger.info("Using ELF file: %s", elf)

    tabulator = Memtab(elf=Path(elf), config=[Path(config)], cache=True)
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
    elf = resolve_elf_path(elf)

    # Create a Memtab instance to extract memory information from the ELF
    # This will auto-generate default config if none exists
    tabulator = Memtab(elf=Path(elf), config=[], cache=True)

    # Get the configuration as a dictionary
    config_dict = tabulator.config.asdict()

    logger.info("Generated configuration based on ELF file: %s", elf)

    # Convert the configuration to YAML string
    yaml_content = yaml.safe_dump(config_dict, default_flow_style=False, sort_keys=False)

    return yaml_content
