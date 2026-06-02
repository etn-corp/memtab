# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Memtab MCP (Model Context Protocol) Server.

This module provides an MCP server interface to the memtab memory analysis tool,
allowing AI assistants to analyze ELF file memory usage through the Model Context Protocol.

Note: This module requires Python >=3.10 due to FastMCP dependency.
"""

try:
    from memtab.mcp.server import (
        create_memtab_config,
        get_memory_table,
        list_elf_files,
        mcp,
        read_elf_file,
    )

    __all__ = [
        "mcp",
        "get_memory_table",
        "create_memtab_config",
        "list_elf_files",
        "read_elf_file",
    ]
except ImportError:
    # FastMCP is not installed - MCP functionality unavailable
    # This is expected when the 'mcp' dependency group is not installed
    __all__ = []
