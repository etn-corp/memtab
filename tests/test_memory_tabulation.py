# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Memory Tabulation of an ELF file feature tests."""

import json
import logging
import os
import platform
import re
import subprocess
from functools import partial
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import yaml
from jsonschema import validate
from pytest import CaptureFixture
from pytest_bdd import given, parsers, then, when
from pytest_bdd import scenario as _scenario_base
from typer.testing import CliRunner

from memtab.cli import app

####################
# boilerplate to shorten the scenario names
####################
feature_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../features")
scenario = partial(_scenario_base, os.path.join(feature_dir, "Memory Tabulation.feature"))

root_dir = os.path.dirname(os.path.abspath(__file__))


def execute_and_log_process(args: str, root: str) -> int:
    env = os.environ
    env["PYTHONUNBUFFERED"] = "True"
    if platform.system() == "Windows":
        if os.getenv("GITHUB_ACTIONS"):
            # explicitly use the one from git, not system's, as WSL is unavailable
            executable = "C:\\Program Files\\Git\\bin\\bash.exe"
        else:
            executable = "bash.exe"  # assume its on the path
    else:
        executable = "/bin/bash"
    # prepend args with our executable and the -c argument for what to call
    cmd_args = [executable, "-c", args]
    with subprocess.Popen(
        cmd_args,
        shell=False,
        cwd=root,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    ) as proc:
        if proc.stdout is None:
            raise RuntimeError("Failed to capture process stdout.")
        while (ret_code := proc.poll()) is None:
            line = proc.stdout.readline().strip()
            logging.info(line)

    return ret_code


################################
# Generic Test Fixtures
################################


def __gen_output_file(elf_file: str) -> Tuple[str, str, List[str]]:
    output_files = []
    if "hello" in elf_file:
        out_name = "hello-world"
    if "cpp" in elf_file:
        out_name = "cpp"
    elif "simple_example" in elf_file:
        out_name = "simple_example"
    else:
        out_name = "zephyr"
    output_file = os.path.join(root_dir, f"{out_name}.json")
    if os.path.exists(output_file):
        os.remove(output_file)
    output_files.append(output_file)
    return out_name, output_file, output_files


def _determine_working_directory(env: Dict[str, str]) -> str:
    """Determine the working directory based on environment variables."""
    if "DEFAULT_ENV" in env:
        return os.path.join(root_dir, "defaults")
    return root_dir


def _build_output_file_args(elf_file: str, working_dir: str) -> Tuple[List[str], List[str], str]:
    """Build arguments for output files and return the list of output files."""
    args = []
    if elf_file:
        out_name, output_file, output_files = __gen_output_file(elf_file)
        args.extend(["--elf", elf_file])
        args.extend(["--json", output_file])
    else:
        output_files = [os.path.join(working_dir, "memtab.json")]  # the default output file
        out_name = "memtab"

    return args, output_files, out_name


def _add_config_args(config_files: List[str]) -> List[str]:
    """Build arguments for configuration files."""
    args = []
    for config_file in config_files:
        args.extend(["--config", config_file])
    return args


def _add_special_arguments(arguments: str, elf_file: str, out_name: str, root_dir: str, output_files: List[str]) -> Tuple[List[str], List[str]]:
    """Process special arguments and add them to the command line."""
    args = []
    for argument in arguments.split():
        if argument == "check":
            args.append("--check")
        elif argument == "map":
            map_file = elf_file.replace(".elf", ".map")
            args.extend(["--map", map_file])
        elif argument == "markdown":
            report_file = os.path.join(root_dir, f"{out_name}.md")
            if os.path.exists(report_file):
                os.remove(report_file)
            args.extend(["--report", "markdown"])
            output_files.append(report_file)
        elif argument == "project":
            args.extend(["--project", "Blinky"])
        else:
            raise ValueError(f"Unknown argument: {argument}")

    return args, output_files


def _prepare_execution_environment(elf_file: str, config_files: List[str], env: Dict[str, str], arguments: str) -> Tuple[str, List[str], List[str]]:
    """Prepare the execution environment for running memtab."""
    working_dir = _determine_working_directory(env)

    # Build base arguments and get output files
    base_args, output_files, out_name = _build_output_file_args(elf_file, working_dir)

    # Add config file arguments
    config_args = _add_config_args(config_files)

    # Add special arguments
    special_args, output_files = _add_special_arguments(arguments, elf_file, out_name, root_dir, output_files)

    # Combine all arguments
    args = base_args + config_args + special_args

    return working_dir, args, output_files


def _prepare_elf_file(elf_file: str, config_files: List[str]) -> Tuple[str, str]:
    """Prepare the ELF file and determine the gcc prefix."""
    if not elf_file:
        elf_file = os.path.join(root_dir, "hello-world.elf")
    if not config_files:
        config_files = [os.path.join(root_dir, "hello-world.yml")]

    gcc_prefix = ""
    for config_file in config_files:
        if not config_file:
            continue

        # read in the gcc_prefix from the config file
        with open(config_file, "r") as stream:
            config = yaml.safe_load(stream)
            if "ELF" in config:
                elf_file = os.path.join(root_dir, "configs", config["ELF"])
                elf_file_path = Path(elf_file).resolve()
                elf_file = str(elf_file_path)
            try:
                gcc_prefix = config["CPU"]["gcc_prefix"]
                break
            except KeyError:
                continue

    return elf_file, gcc_prefix


def _count_symbols(elf_file: str, gcc_prefix: str) -> int:
    """Count the number of symbols in the ELF file."""
    nm_symbols_cmd = [f"{gcc_prefix}nm", "-SlC", elf_file]
    symbols_result = subprocess.check_output(nm_symbols_cmd).decode("utf-8")
    return len(symbols_result.splitlines())


def _should_ignore_section(name: str, section_type: str) -> bool:
    """Determine if a section should be ignored."""
    # Check disallowed names
    disallowed_names = ["debug", "ARM", "eh_frame", "dynsym", "comment"]
    for disallowed_name in disallowed_names:
        if disallowed_name in name:
            return True

    # Check disallowed types
    disallowed_types = ["TAB"]
    for disallowed_type in disallowed_types:
        if disallowed_type in section_type:
            return True

    return False


def _count_sections(elf_file: str, gcc_prefix: str) -> int:
    """Count the number of sections in the ELF file."""
    readelf_sections_cmd = [f"{gcc_prefix}readelf", "-SW", elf_file]
    sections_result = subprocess.check_output(readelf_sections_cmd).decode("utf-8")
    sections = [section.strip() for section in sections_result.splitlines()]

    # Regex pattern to parse readelf -SW output, handles section names with spaces
    pattern = re.compile(
        r"^\s*\[\s*\d+\]\s+"  # [Nr] with optional whitespace
        r"(\S.*?)\s+"  # Name (non-greedy, can contain spaces)
        r"(\S+)\s+"  # Type
        r"([0-9a-fA-F]+)\s+"  # Addr
        r"([0-9a-fA-F]+)\s+"  # Off
        r"([0-9a-fA-F]+)\s+"  # Size
    )

    sections_count = 0
    for section in sections:
        if "[Nr]" in section:
            continue

        match = pattern.match(section)
        if match:
            name, section_type, addr_str, off_str, size_str = match.groups()
            name = name.strip()
            addr = int(addr_str, 16)
            size = int(size_str, 16)

            if not _should_ignore_section(name, section_type) and addr != 0 and size != 0:
                sections_count += 1

    return sections_count


def generate_ground_truth(elf_file: str, config_files: List[str]) -> Dict[str, int]:
    """Generate a ground truth from the given ELF file, which we can use
    to perform some rudimentary checks on the output, such as
    the total # of symbols (even if addr and size are not checked),
    and the total # of sections
    """
    ground_truth = {
        "symbols": 0,
        "sections": 0,
    }

    elf_file, gcc_prefix = _prepare_elf_file(elf_file, config_files)
    ground_truth["symbols"] = _count_symbols(elf_file, gcc_prefix)
    ground_truth["sections"] = _count_sections(elf_file, gcc_prefix)

    return ground_truth


################################
# BDD Scenarios
################################
@scenario("Memory tabulation of an ELF file")
def test_memory_tabulation_of_an_elf_file() -> None:
    """Memory tabulation of an ELF file."""


@scenario("Supplementing the ELF file with a Map File")
def test_supplementing_the_elf_file_with_a_map_file() -> None:
    """Supplementing the ELF file with a Map File."""


@scenario("LMA sections in Flash are accounted for in the Flash region spare")
def test_lma_sections_in_flash_accounted_for_in_spare() -> None:
    """LMA sections in Flash are accounted for in the Flash region spare."""


@scenario("ARM unwind sections are attributed to owning symbols")
def test_arm_unwind_sections_are_attributed_to_owning_symbols() -> None:
    """ARM unwind sections are attributed to owning symbols."""


################################
# BDD Given Statements
################################
@given("an ELF file", target_fixture="elf_file")
def an_elf_file() -> Generator[Optional[str], None, None]:
    """an ELF file."""
    yield os.path.join(root_dir, "inputs", "blinky.elf")


@given(parsers.re("a (?P<toolchain>[a-zA-Z0-9._]*) ELF file"), target_fixture="elf_file")
def given_some_elf_file(toolchain: str) -> Generator[Optional[str], None, None]:
    """I have an ELF file."""
    toolchain_to_elf = {"x86": "hello-world.elf", "no_cfg_cube": "simple_example.elf", "blinky": "blinky.elf", "cpp": "cpp.elf"}
    elf_file = None
    if toolchain in toolchain_to_elf:
        elf_file = os.path.join(root_dir, "inputs", toolchain_to_elf[toolchain])
    elif toolchain == "local_source":
        # this one is more complicated.  here we actually have to BUILD the local_source example to get the ELF file, its not checked in.

        build_result = execute_and_log_process(
            "gcc -g main.c -o local_source.elf",
            os.path.join(root_dir, "inputs", "local"),
        )
        if build_result != 0:
            raise RuntimeError("Failed to build the local_source example.")
        elf_file = os.path.join(root_dir, "inputs", "local", "local_source.elf")
    else:
        elf_file = os.path.join(root_dir, "inputs", "blinky.elf")
    yield elf_file


@given("a map file", target_fixture="map_file")
def given_map_file() -> Generator[Optional[str], None, None]:
    map_file = os.path.join(root_dir, "inputs", "blinky.map")
    yield map_file


@given(
    parsers.re("(?P<configuration>[a-zA-Z0-9._ ]*)files describing the memory layout of the target device, the toolchain, and the categories and subcategories of memory"),
    target_fixture="config_files",
)
def given_configuration_files(configuration: str) -> Generator[List[Optional[str]], None, None]:
    """<configuration> file(s) describing the memory layout of the target device, the toolchain, and the categories and subcategories of memory."""
    configuration = configuration.strip()  # remove leading/trailing whitespace

    config_words = configuration.split(" ")
    config_files = []
    for word in config_words:
        config_lookup = {
            "x86": "hello-world.yml",
            "arm": "blinky.yml",
            # Alias used by the ARM attribution scenario; we do not require a separate file.
            "blinky_arm": "blinky.yml",
            "cube": "simple_example.yml",
            "configuration": "simple_example.yml",
            "local_source": "local_source.yml",
            "blinky": "blinky.yml",
            "blinky_include": "blinky_include.yml",
            "blinky_with_elf": "blinky_with_elf.yml",
            "blinky_no_project": "blinky_no_project.yml",
            "cpp": "cpp.yml",
        }
        config_file = os.path.join(root_dir, "configs", config_lookup[word]) if word else None
        config_files.append(config_file)
    yield config_files


@given(parsers.re("(?P<environment>[a-zA-Z ]*)variables"), target_fixture="env")
def given_environment_variables(environment: str) -> Generator[Dict[str, str], None, None]:
    """environment variables"""
    environment = environment.strip()  # remove leading/trailing whitespace
    my_env = os.environ.copy()
    # explicitly blank GITHUB_ACTIONS out. this is necessary if we are running these tests inside a GHA.
    # when GITHUB_ACTIONS is set to not true, we don't need to explicitly manipulate any of the other variables
    my_env["GITHUB_ACTIONS"] = ""
    if "GitHub Action" in environment:
        # once this is true, we can assume we are in a GitHub Action, and several other variables must be available as well
        # we set these here for 2 reasons. 1 - so we have static/known values, and 2 - to overwrite any existing values that
        # a real GHA may be setting if these tests are run in GHA
        # these are documented here:
        # https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
        my_env["GITHUB_ACTIONS"] = "true"
        my_env["GITHUB_REPOSITORY"] = "test/repo"
        my_env["GITHUB_SHA"] = "beefbeefbeefbeefbeefbeefbeefbeefbeefbeef"
        my_env["GITHUB_RUN_ID"] = "1234567890"
        my_env["GITHUB_RUN_ATTEMPT"] = "42"
        my_env["GITHUB_WORKFLOW"] = "test_workflow"
        my_env["GITHUB_REF"] = "refs/heads/main"
        my_env["GITHUB_EVENT_NAME"] = "push"
    elif "Memtab Env" in environment:
        my_env["MEMTAB_ELF"] = os.path.join(root_dir, "hello-world.elf")
        my_env["MEMTAB_YML"] = os.path.join(root_dir, "hello-world.yml")
    elif "Memtab Proj Env" in environment:
        my_env["MEMTAB_ELF"] = os.path.join(root_dir, "blinky.elf")
        my_env["MEMTAB_YML"] = os.path.join(root_dir, "blinky_no_project.yml")
        my_env["MEMTAB_PROJECT"] = "Blinky"
    elif "Defaults" in environment:
        # this is a bit odd, but we just put a special variable in the env as a "flag" to downstream tests
        # to indicate that we should run in a different folder, so we don't mess up other tests that rely on
        # the default files being present.
        my_env["DEFAULT_ENV"] = "1"

    yield my_env


################################
# BDD When Statements
################################
@when(
    parsers.re("(?P<agent>[A-Z]*) run the memory tabulation command with (?P<arguments>[a-z-]*) arguments"),
    target_fixture="results",
)
def when_agent_runs_memory_tabulation_command(
    agent: str, arguments: str, elf_file: str, config_files: List[str], env: Dict[str, str], capsys: CaptureFixture
) -> Generator[List[str], None, None]:
    """I run the memory tabulation command."""
    runner = CliRunner()

    # In the main function:
    working_dir, args, output_files = _prepare_execution_environment(elf_file, config_files, env, arguments)
    with capsys.disabled():  # this is needed so stdout/logging can be captured by the runner, instead of pytest.
        current_dir = os.getcwd()
        os.chdir(working_dir)
        try:
            runner.invoke(app, args, catch_exceptions=False, color=True, env=env)
        finally:
            os.chdir(current_dir)
    yield output_files
    for outtfile in output_files:
        if os.path.exists(outtfile):
            os.remove(outtfile)


################################
# BDD Then Statements
################################
@then(parsers.re("I should see the memory tabulation of the ELF file broken down into (?P<output>[a-zA-Z\s]+) output."))
def then_tabulation_should_contain_elf_info(output: str, results: List[str]) -> None:
    """I should see the memory tabulation of the ELF file broken down into <output> output."""

    def verify_json(output: str, results: List[str]) -> None:
        if "JSON" in output:
            for result in results:
                if ".json" in result:
                    with open(result, "r") as stream:
                        json_response = json.load(stream)
                        # validate the JSON against schema
                        schema_dir = os.path.join(root_dir, "../src/memtab/schemas")
                        output_schema_path = os.path.join(schema_dir, "memtab_schema.json")
                        with open(output_schema_path, "r") as stream:
                            output_schema = json.load(stream)
                        validate(json_response, output_schema)

    def verify_markdown(output: str, results: List[str]) -> None:
        if "markdown" in output:
            for result in results:
                if ".md" in result:
                    md_response = result
                    # verify we got an markdown file
                    assert os.path.exists(md_response)

    verify_json(output, results)
    verify_markdown(output, results)


@then("the memory tabulation should contain additional information only available in the map file.")
def then_tabulation_should_contain_map_info(results: List[str]) -> None:
    def verify_map_file_contents_in_json(json_payload: Any) -> None:
        map_dict = {
            "runqueue_bitcache": False,
        }
        for symbol in json_payload["symbols"]:
            for my_key in map_dict.keys():
                if symbol["symbol"] == my_key:
                    map_dict[my_key] = True
                    break

        # Assert that all the expected symbols from the map file are present in the BSS section
        assert all(map_dict.values()), f"Not all map file symbols were found: {[k for k, v in map_dict.items() if not v]}"

    for result in results:
        if ".json" in result:
            with open(result, "r") as stream:
                json_response = json.load(stream)
                verify_map_file_contents_in_json(json_response)


@then("sections with a load address in Flash but a runtime address in RAM are counted toward Flash spare.")
def then_lma_sections_counted_in_flash_spare(results: List[str]) -> None:
    """Verify that sections with LMA in Flash (e.g. .relocate) are accounted for in Flash spare.

    The blinky.map has .relocate with VMA in RAM (0x20000200) and LMA in Flash (0x0800200c,
    size 0x34 = 52 bytes). Before this fix those 52 bytes were invisible to the spare
    calculation. This test checks that they are now counted.
    """
    for result in results:
        if ".json" not in result:
            continue
        with open(result, "r") as stream:
            data = json.load(stream)

        sections = data["elf_sections"]
        regions = data["regions"]

        def _addr(val: Any) -> int:
            return int(str(val), 16) if isinstance(val, str) and str(val).startswith("0x") else int(val)

        # Locate the Flash region by region type ("Flash"), not by name — the config name
        # (e.g. "FLASH") is normalised to lowercase in the output, so using region type is robust.
        flash = next((r for r in regions if r.get("region") == "Flash"), None)
        assert flash is not None, "Flash region not found in output"
        flash_start = _addr(flash["start"])
        flash_end = _addr(flash["end"])
        flash_spare = _addr(flash["spare"])

        # Find .relocate and verify its LMA is populated and falls in Flash
        relocate = next((s for s in sections if s["name"] == ".relocate"), None)
        assert relocate is not None, ".relocate section missing from elf_sections"
        lma = _addr(relocate.get("lma", 0))
        assert lma != 0, ".relocate lma should be non-zero (map file should supply it)"
        assert lma != _addr(relocate["address"]), ".relocate lma should differ from its VMA"
        assert flash_start <= lma <= flash_end, f".relocate lma 0x{lma:x} should fall within Flash [{flash_start:#x}, {flash_end:#x}]"

        # The actual Flash usage is: (physical region size) - spare.
        # spare is initialised from the config size (end - start), so we use end - start here
        # rather than the 'size' field (which carries a +1 from inclusive-end encoding).
        actual_flash_usage = (flash_end - flash_start) - flash_spare

        # Expected usage = VMA sections in Flash + non-NOBITS LMA sections in Flash
        # (NOBITS sections like .bss have no bytes at their LMA even though the
        # linker assigns one, so they must not be counted.)
        expected_flash_usage = sum(
            _addr(s["size"])
            for s in sections
            if (flash_start <= _addr(s["address"]) <= flash_end)
            or (
                _addr(s.get("lma", 0)) != 0
                and _addr(s.get("lma", 0)) != _addr(s["address"])
                and flash_start <= _addr(s.get("lma", 0)) <= flash_end
                and s.get("type", "") != "NOBITS"
            )
        )
        assert actual_flash_usage == expected_flash_usage, (
            f"Flash usage {actual_flash_usage} does not match expected {expected_flash_usage} "
            f"(sections by VMA + non-NOBITS LMA in Flash). .relocate (size={_addr(relocate['size'])}) "
            f"at LMA=0x{lma:x} should be included."
        )


@then("ARM unwind table bytes should be attributed to owning symbols.")
def then_arm_unwind_tables_attributed_to_symbols(results: List[str]) -> None:
    """Verify exidx/extab bytes are attributed to symbols and reconcile with section sizes."""

    def _addr(value: Any) -> int:
        return int(str(value), 16) if isinstance(value, str) and str(value).startswith("0x") else int(value)

    for result in results:
        if ".json" not in result:
            continue

        with open(result, "r") as stream:
            data = json.load(stream)

        sections = data["elf_sections"]
        symbols = data["symbols"]

        exidx_section = next((s for s in sections if s["name"] == ".ARM.exidx"), None)
        extab_section = next((s for s in sections if s["name"] == ".ARM.extab"), None)
        assert exidx_section is not None and extab_section is not None, "Expected .ARM.exidx and .ARM.extab to be present in elf_sections output"

        symbol_exidx_total = sum(_addr(symbol.get("exidx_size", 0)) for symbol in symbols)
        symbol_extab_total = sum(_addr(symbol.get("extab_size", 0)) for symbol in symbols)

        assert any("exidx_size" in symbol for symbol in symbols), "Symbols are missing exidx_size"
        assert any("extab_size" in symbol for symbol in symbols), "Symbols are missing extab_size"
        assert any(_addr(symbol.get("exidx_size", 0)) > 0 for symbol in symbols), "Expected at least one symbol with non-zero exidx_size"

        assert symbol_exidx_total == _addr(exidx_section["size"]), f"Sum of symbol exidx_size ({symbol_exidx_total}) should match .ARM.exidx size ({_addr(exidx_section['size'])})"
        assert symbol_extab_total == _addr(extab_section["size"]), f"Sum of symbol extab_size ({symbol_extab_total}) should match .ARM.extab size ({_addr(extab_section['size'])})"


@then(parsers.re("the (?P<output>[a-zA-Z\s]+) should be correlated to a ground truth."))
def then_output_should_be_correlated_to_ground_truth(elf_file: str, config_files: List[str], output: str, results: List[str]) -> None:
    """the output should be correlated to a ground truth."""

    symbol_count, section_count = generate_ground_truth(elf_file, config_files).values()

    assert symbol_count > 0, "Expected at least one symbol in the ELF file."
    assert section_count > 0, "Expected at least one section in the ELF file."

    if "JSON" in output:
        for result in results:
            if ".json" in result:
                with open(result, "r") as stream:
                    json_response = json.load(stream)
                    # check the number of symbols
                    assert len(json_response["symbols"]) <= symbol_count, f"Expected at most {symbol_count} symbols, got {len(json_response['symbols'])} symbols in {result}"
                    # check the number of sections
                    assert len(json_response["elf_sections"]) == section_count, (
                        f"Expected exactly {section_count} sections, got {len(json_response['elf_sections'])} sections in {result}"
                    )
