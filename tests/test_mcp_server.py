# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""MCP Server feature tests."""

import os
from functools import partial
from pathlib import Path
from typing import Any, Dict, Generator, List

import pytest
from pytest_bdd import given, scenario, then, when

# Skip all tests in this module if fastmcp is not installed
pytest.importorskip("fastmcp", reason="MCP server tests require fastmcp (install with: uv sync --group mcp)")

from memtab.mcp.discovery import find_elf_files  # noqa: E402
from memtab.mcp.server import _enforce_allowed_file_access, _enforce_elf_size_limit, _get_memory_table  # noqa: E402

####################
# boilerplate to shorten the scenario names
####################
feature_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../features")
scenario = partial(scenario, os.path.join(feature_dir, "MCP Server.feature"))

root_dir = os.path.dirname(os.path.abspath(__file__))


################################
# Generic Test Fixtures
################################


################################
# BDD Scenarios
################################
@scenario("MCP Server")
def test_mcp_server() -> None:
    """MCP Server."""


################################
# BDD Given Statements
################################
@given("an elf file", target_fixture="elf_file")
def _() -> Generator[str, None, None]:
    """an elf file."""
    yield os.path.join(root_dir, "inputs", "hello-world.elf")


################################
# BDD When Statements
################################
@when("I ask copilot about the memory usage of that elf file", target_fixture="response")
def _(elf_file: str, monkeypatch: pytest.MonkeyPatch) -> List[Dict[str, Any]]:
    """I ask copilot about the memory usage of that elf file."""
    # Set MEMTAB_CONFIG to use the test config file to avoid picking up action.yml
    monkeypatch.setenv("MEMTAB_CONFIG", os.path.join(root_dir, "configs", "hello-world.yml"))
    return _get_memory_table(elf_file)


################################
# BDD Then Statements
################################
@then("I should get a response with the memory usage of the elf file in list format")
def _(response: List[Dict[str, Any]]) -> None:
    """I should get a response with the memory usage of the elf file in list format."""
    assert isinstance(response, list)


def test_read_elf_file_rejects_path_outside_allowed_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MCP resource rejects file paths that escape allowed roots."""
    allowed_root = tmp_path / "allowed"
    outside_root = tmp_path / "outside"
    allowed_root.mkdir()
    outside_root.mkdir()

    outside_elf = outside_root / "outside.elf"
    outside_elf.write_bytes(b"elf")

    monkeypatch.setenv("MEMTAB_ALLOWED_ROOTS", str(allowed_root))

    with pytest.raises(PermissionError):
        _enforce_allowed_file_access(str(outside_elf), expected_suffixes=(".elf",))


def test_read_elf_file_rejects_large_elf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MCP resource rejects ELF files larger than configured max bytes."""
    elf_file = tmp_path / "large.elf"
    elf_file.write_bytes(b"01234567890")

    monkeypatch.setenv("MEMTAB_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setenv("MEMTAB_MAX_ELF_BYTES", "5")

    with pytest.raises(ValueError, match="too large"):
        _enforce_elf_size_limit(elf_file)


def test_list_elf_files_respects_default_search_depth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MCP discovery should honor bounded default depth."""
    root_elf = tmp_path / "root.elf"
    root_elf.write_bytes(b"elf")

    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_elf = nested_dir / "nested.elf"
    nested_elf.write_bytes(b"elf")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MEMTAB_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setenv("MEMTAB_MCP_DEFAULT_SEARCH_DEPTH", "0")

    discovered_paths = find_elf_files(start_dir=str(tmp_path), max_depth=None)
    names = {Path(path).name for path in discovered_paths}

    assert root_elf.name in names
    assert nested_elf.name not in names
