# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""ObjDump parser module for memtab.

This module provides parsing functionality for the output of the 'objdump' command,
which displays information about object files.
"""

import re

from memtab.models import Section
from memtab.parsers.base import MemtabGnuBinUtilsParser


class ObjDumpParser(MemtabGnuBinUtilsParser):
    """Parser for the output of the 'objdump' command.

    This class parses the output of the 'objdump' command to extract section
    and symbol information from object files.
    """

    command = "objdump"
    args = ["-wh"]

    def parse_output_into_results(self) -> None:
        """Parse the objdump output and populate the sections and symbols lists."""
        section_pattern = re.compile(r"^\s*(\d+)\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+).*")

        section_headers_mode = False

        for line in self.raw_data.split("\n"):
            if "Sections:" in line:
                section_headers_mode = True
                continue
            elif "SYMBOL TABLE:" in line:
                section_headers_mode = False
                continue

            if section_headers_mode and "Idx" not in line and line.strip():

                def process_objdump_line(line: str) -> None:
                    match = section_pattern.match(line)
                    if match:
                        # Parse section data from the line
                        section_name = match.group(2)
                        section_size = int(match.group(3), 16)
                        section_vma = int(match.group(4), 16)
                        # section_lma = int(match.group(5), 16)

                        # Extract flags - typically at the end of the line
                        flags = ""
                        if "CONTENTS" in line:
                            flags += "C"
                        if "ALLOC" in line:
                            flags += "A"
                        if "LOAD" in line:
                            flags += "L"
                        if "DATA" in line:
                            flags += "D"
                        if "CODE" in line:
                            flags += "X"

                        self.result.sections.append(Section(name=section_name, address=section_vma, size=section_size, flags=flags))

                process_objdump_line(line)
