# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Creating Visualizations feature tests."""

import json
import os
import tempfile
from functools import partial
from typing import Any, Generator

from click.testing import Result
from hypothesis.strategies import SearchStrategy
from hypothesis_jsonschema import from_schema
from pytest import CaptureFixture
from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)
from typer.testing import CliRunner

from memtab.cli import vizapp

####################
# boilerplate to shorten the scenario names
####################
feature_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../features")
scenario = partial(scenario, os.path.join(feature_dir, "Creating Visualizations.feature"))

root_dir = os.path.dirname(os.path.abspath(__file__))

################################
# Generic Test Fixtures
################################


################################
# BDD Scenarios
################################
@scenario("Generating Visuals from Memtab Output")
def test_generating_visuals_from_memtab_output() -> None:
    """Generating Visuals from Memtab Output."""


################################
# BDD Given Statements
################################
@given("a memtab JSON file", target_fixture="input")
def _() -> Generator[str, None, None]:
    """a memtab JSON file."""

    def _gen_compliant_json_file() -> Any:
        # Load the schema from the project
        schema_path = os.path.join(root_dir, "../src/memtab/schemas/memtab_schema.json")
        with open(schema_path, "r") as f:
            schema = json.load(f)

        example_strategy: SearchStrategy[Any] = from_schema(schema)
        return example_strategy.example()

    example = _gen_compliant_json_file()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(example, f, indent=2)
        temp_file_path = f.name

    yield temp_file_path
    report_filename = ""
    if example["metadata"]["filename"]:
        report_filename = example["metadata"]["filename"].replace(".elf", "")
        report_filename += ".md"
    elif os.path.exists("memtab_report.md"):
        report_filename = "memtab_report.md"
    if report_filename and os.path.exists(report_filename):
        os.remove(report_filename)
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


################################
# BDD When Statements
################################
@when("I run the memtab visualizer tool with a report specified", target_fixture="result")
def _(input: str, capsys: CaptureFixture) -> Generator[Result, None, None]:
    """I run the memtab visualizer tool with a report specified."""
    with capsys.disabled():
        yield CliRunner().invoke(vizapp, ["--input", input, "--report", "markdown"], catch_exceptions=False, color=True)


################################
# BDD Then Statements
################################
@then("I should see a visualization generated from the memtab output")
def _(result: Result) -> None:
    """I should see a visualization generated from the memtab output."""
    assert result.exit_code == 0
