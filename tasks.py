# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Disparate tasks to support memtab development and testing."""

import os
from pathlib import Path

from invoke import context, task


@task(aliases=["v"])
def get_version(c: context) -> None:
    import toml

    with open("pyproject.toml", "r") as f:
        data = toml.load(f)
        print(data["project"]["version"])


@task(aliases=["m"])
def map_regex_tester(c: context) -> None:
    """Test out regexes for the map file parser."""
    import re

    map_file = Path("map_lines.txt")
    with open(map_file, "r") as f:
        content = f.read()

    section_regex = re.compile(r"\n(?P<section>[a-zA-Z._]+)(\s+|\n)0x(?P<offset>[0-9a-f]+)\s+0x(?P<size>[0-9a-f/]+)(?P<comment>.*)")

    for match in section_regex.finditer(content):
        section = match.group("section").strip()
        offset = int(match.group("offset"), 16)
        size = int(match.group("size"), 16)
        comment = match.group("comment").strip()
        if offset and size:
            print(f"Region: {section}, Start: 0x{offset:08x}, Size: {size}, Flags: {comment}")

    subsection_regex = re.compile(
        r"\n\s.(?P<name>[0-9a-zA-Z._]+)(\s+|\n)0x(?P<offset>[0-9a-f]+)\s+0x(?P<size>[0-9a-f]+)(\s+|\n)(?P<path>[a-zA-Z:\\\/_.\-0-9]+)\(*(?P<file>[a-zA-Z._0-9\-]*)\)*"
    )

    for match in subsection_regex.finditer(content):
        name = match.group("name").strip()
        offset = int(match.group("offset"), 16)
        size = int(match.group("size"), 16)
        path = match.group("path").strip()
        file = match.group("file").strip()

        words = name.split(".")
        section = words[0]

        if len(words) > 2:
            symbol_name = words[2]
        elif len(words) == 2:
            symbol_name = words[1]
        else:
            symbol_name = file.replace(".o", "")

        if not file:
            object_file = path
        else:
            object_file = file
        if offset and size:
            print(f"section: {section}, symbol: {symbol_name}, addr: 0x{offset:08x}, size: {size}, object_file: {object_file}")


@task(aliases=["mtr"])
def metrics(c: context) -> None:
    """Gather basic code metrics, such as lines of code, complexity, etc.
    Uses the radon package, as well as a coverage.xml file if it exists."""
    import json

    from radon.cli import Config
    from radon.cli.harvest import CCHarvester, HCHarvester, MIHarvester, RawHarvester
    from radon.complexity import SCORE
    from rich.pretty import pprint

    root_dir = os.path.dirname(os.path.abspath(__file__))
    src_dirs = [os.path.join(root_dir, "src/memtab/")]

    radon_config = Config(
        exclude="",
        ignore="",
        order=SCORE,
        no_assert=False,
        show_closures=True,
        min="A",
        max="F",
        multi=True,
        by_function=True,
    )
    cc = CCHarvester(src_dirs, config=radon_config)
    raw = RawHarvester(src_dirs, config=radon_config)
    mi = MIHarvester(src_dirs, config=radon_config)
    hc = HCHarvester(src_dirs, config=radon_config)

    raw_json = json.loads(raw.as_json())
    cc_json = json.loads(cc.as_json())
    mi_json = json.loads(mi.as_json())
    hc_json = json.loads(hc.as_json())

    assert len(raw_json) == len(mi_json) == len(hc_json), f"The JSON outputs from radon do not match in length: {len(raw_json)}, {len(mi_json)}, {len(hc_json)}"
    assert len(cc_json) <= len(raw_json), f"The Cyclomatic Complexity JSON outputs from radon do not match in length: {len(cc_json)}, {len(raw_json)}"
    overall = {}

    for filename in raw_json:
        overall[filename] = {
            "raw": raw_json[filename],
            "cc": cc_json.get(filename, {}),
            "mi": mi_json[filename],
            "hc": hc_json[filename],
        }

    pprint(overall)
    with open("metrics.json", "w") as stream:
        json.dump(overall, stream, indent=4)

    if os.path.exists("coverage.xml"):
        pass
