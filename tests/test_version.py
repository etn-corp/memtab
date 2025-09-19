# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Version Reporting feature tests."""

import os
from functools import partial
from importlib.metadata import version as get_version
from typing import Generator

from pytest import CaptureFixture
from pytest_bdd import given, scenario, then, when
from typer import Typer
from typer.testing import CliRunner

from memtab.cli import app

####################
# boilerplate to shorten the scenario names
####################
feature_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../features")
scenario = partial(scenario, os.path.join(feature_dir, "Version Reporting.feature"))

root_dir = os.path.dirname(os.path.abspath(__file__))


################################
# Generic Test Fixtures
################################


################################
# BDD Scenarios
################################
@scenario("Version Reporting")
def test_version_reporting() -> None:
    """Version Reporting."""


################################
# BDD Given Statements
################################
@given("I have the memory tabulator package", target_fixture="memtab")
def _() -> Generator[Typer, None, None]:
    """I have the memory tabulator package."""

    yield app


################################
# BDD When Statements
################################
@when("I run the version command", target_fixture="version")
def _(memtab: Typer, capsys: CaptureFixture) -> Generator[str, None, None]:
    """I run the version command."""
    runner = CliRunner()
    with capsys.disabled():  # this is needed so stdout/logging can be captured by the runner, instead of pytest.
        request = runner.invoke(memtab, ["--version"])
        yield request.stdout


################################
# BDD Then Statements
################################
@then("the version should be reported")
def _(version: str) -> None:
    """the version should be reported."""
    assert version.strip() == get_version("memtab")
