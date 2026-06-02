# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""MCP Server feature tests."""

import os
from functools import partial
from typing import Any, Dict, Generator, List

import pytest
from pytest_bdd import given, scenario, then, when

# Skip all tests in this module if fastmcp is not installed
pytest.importorskip("fastmcp", reason="MCP server tests require fastmcp (install with: uv sync --group mcp)")

from memtab.mcp.server import _get_memory_table  # noqa: E402

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
