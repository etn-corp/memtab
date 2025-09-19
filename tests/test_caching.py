# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Caching data to speed up repeated runs feature tests."""

import logging
import os
import random
import string
import time
from functools import partial
from typing import Dict, Generator, List, Union

from appdirs import (
    user_cache_dir,  # there is some "implementation awareness" here... but I think its ok
)
from pytest import CaptureFixture, fixture
from pytest_bdd import given, scenario, then, when
from typer import Typer
from typer.testing import CliRunner, Result

from memtab.cli import app

####################
# boilerplate to shorten the scenario names
####################
feature_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../features")
scenario = partial(scenario, os.path.join(feature_dir, "Caching.feature"))

root_dir = os.path.dirname(os.path.abspath(__file__))


################################
# Generic Test Fixtures
################################
@fixture(scope="module")
def memtab_cache_dir() -> Generator[str, None, None]:
    """Fixture to provide the memtab cache directory."""
    yield user_cache_dir("memtab", "memtab")  # these names have to match what is in memtab.py.  Is there a better way? Config data?


################################
# BDD Scenarios
################################
@scenario("Caching command output")
def test_caching_command_output() -> None:
    """Caching command output."""


@scenario("Clearing the cache")
def test_clearing_the_cache() -> None:
    """Clearing the cache."""


################################
# BDD Given Statements
################################
@given("I have a memtab instance", target_fixture="memtab")
def given_memtab_instance() -> Generator[Typer, None, None]:
    """I have a memtab instance."""
    yield app


@given("the cache is empty")
def given_the_cache_is_empty(memtab_cache_dir: str) -> None:
    """the cache is empty."""
    if os.path.exists(memtab_cache_dir):
        for file in os.listdir(memtab_cache_dir):
            os.remove(os.path.join(memtab_cache_dir, file))
        os.rmdir(memtab_cache_dir)


@given("the cache is populated")
def given_the_cache_is_populated(memtab_cache_dir: str) -> None:
    """the cache is populated."""
    os.makedirs(memtab_cache_dir, exist_ok=True)
    # Create a random file name and add some content to simulate a cached file
    random_chars = "".join(random.choice(string.ascii_lowercase) for _ in range(10))
    cache_file_name = f"cache_{random_chars}.dat"
    cache_file_path = os.path.join(memtab_cache_dir, cache_file_name)

    with open(cache_file_path, "w") as f:
        f.write("some cached data")


################################
# BDD When Statements
################################
@when('I run the command "memtab --clean"', target_fixture="memtab_clean_command")
def when_i_run_the_command_memtab_clean(memtab: Typer, capsys: CaptureFixture) -> Generator[Result, None, None]:
    """I run the command "memtab --clean"."""
    with capsys.disabled():  # this is needed so stdout/logging can be captured by the runner, instead of pytest.
        runner = CliRunner()
        yield runner.invoke(memtab, ["--clean"])


@when("I run the same memtab command twice", target_fixture="memtab_command_results")
def when_i_run_the_same_memtab_command_twice(memtab: Typer, capsys: CaptureFixture) -> Generator[List[Dict[str, Union[float, Result]]], None, None]:
    """I run the same memtab command twice."""
    elf_file = os.path.join(root_dir, "inputs", "simple_example.elf")
    cfg_file = os.path.join(root_dir, "config", "simple_example.yml")
    args = ["--elf", elf_file, "--config", cfg_file]
    with capsys.disabled():  # this is needed so stdout/logging can be captured by the runner, instead of pytest.
        runner = CliRunner()
        first_start_time = time.time()
        first_run = runner.invoke(memtab, args)
        intermediate_time = time.time()
        second_run = runner.invoke(memtab, args)
        stop_time = time.time()
        first_cmd = {
            "duration": intermediate_time - first_start_time,
            "result": first_run,
        }
        second_cmd = {
            "duration": stop_time - intermediate_time,
            "result": second_run,
        }
        yield [first_cmd, second_cmd]


################################
# BDD Then Statements
################################
@then("the cache should be cleared")
def then_the_cache_should_be_cleared(memtab_cache_dir: str, memtab_clean_command: Result) -> None:
    """the cache should be cleared."""
    assert memtab_clean_command.exit_code == 0, "Cache clearing command failed."
    assert os.path.exists(memtab_cache_dir), "Cache directory does not exist."
    assert len(os.listdir(memtab_cache_dir)) == 0, f"Cache directory ({memtab_cache_dir})is not empty after clearing."


@then("the second run should be faster than the first")
def then_the_second_run_should_be_faster_than_the_first(memtab_command_results: List[Dict[str, Union[float, Result]]]) -> None:
    """the second run should be faster than the first."""
    first_cmd = memtab_command_results[0]
    second_cmd = memtab_command_results[1]
    first_time = first_cmd["duration"]
    second_time = second_cmd["duration"]
    first_result: Result = first_cmd["result"]
    second_result: Result = second_cmd["result"]
    assert first_result.exit_code == 0, f"First run failed with exit code {first_result.exit_code}."
    assert second_result.exit_code == 0, f"Second run failed with exit code {second_result.exit_code}."
    message = f"first run took {first_time:.2f}s, second run took {second_time:.2f}s"
    logging.info(message)
    assert second_time < first_time, f"Second run took {second_time:.2f}s, which is not faster than the first run ({first_time:.2f}s)."
