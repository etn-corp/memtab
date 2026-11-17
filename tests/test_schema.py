# SPDX-FileCopyrightText: 2026 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Output schema tests."""

import json
import os

import pytest
from jsonschema import Draft7Validator

import memtab

schema_path = os.path.join(os.path.dirname(memtab.__file__), "schemas", "memtab_schema.json")
with open(schema_path, "r") as stream:
    section_type_schema = json.load(stream)["$defs"]["elf_section"]["properties"]["type"]

validator = Draft7Validator(section_type_schema)


@pytest.mark.parametrize(
    "section_type",
    [
        "PROGBITS",
        "NOBITS",
        "ARM_EXIDX",
        "ARM_ATTRIBUTES",
        # Architecture-specific attribute sections emitted by `readelf -SW`.
        "RISCV_ATTRIBUTES",  # RISC-V (e.g. esp32c6)
        "XTENSA_INFO",  # Xtensa (e.g. esp32)
    ],
)
def test_elf_section_type_enum_accepts_known_types(section_type: str) -> None:
    """The elf_section type enum accepts known architecture section types."""
    assert validator.is_valid(section_type)


@pytest.mark.parametrize("section_type", ["progbits", "UNKNOWN_TYPE", ""])
def test_elf_section_type_enum_rejects_unknown_types(section_type: str) -> None:
    """The elf_section type enum rejects values outside the known set."""
    assert not validator.is_valid(section_type)
