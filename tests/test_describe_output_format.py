# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Provide a file describing the output data format feature tests."""

import os
from functools import partial
from typing import Any, Generator

from pytest_bdd import given, scenario, then, when

from memtab.memtab import Memtab

####################
# boilerplate to shorten the scenario names
####################
feature_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../features")
scenario = partial(scenario, os.path.join(feature_dir, "Describe Output Format.feature"))

root_dir = os.path.dirname(os.path.abspath(__file__))


################################
# Generic Test Fixtures
################################


################################
# BDD Scenarios
################################
@scenario("Provide a file describing the output data format")
def test_provide_a_file_describing_the_output_data_format() -> None:
    """Provide a file describing the output data format."""


################################
# BDD Given Statements
################################
@given("I have the memory tabulator package", target_fixture="memtab")
def given_memtab_package() -> Generator[Memtab, None, None]:
    """I have the memory tabulator package."""
    orig_dir = os.getcwd()
    os.chdir(root_dir)
    yield Memtab()
    os.chdir(orig_dir)


################################
# BDD When Statements
################################
@when("I run the schema command", target_fixture="schema")
def when_i_run_the_schema_command(memtab: Memtab) -> Generator[Any, None, None]:
    """I run the schema command."""
    yield memtab.schema


################################
# BDD Then Statements
################################
@then("I should be provided the schema file")
def then_i_should_be_provided_the_schema_file(schema: Any) -> None:
    """I should be provided the schema file."""
    assert len(schema) > 0
