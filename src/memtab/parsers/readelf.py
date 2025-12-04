# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""ReadElf parser module for memtab.

This module provides parsing functionality for the output of the 'readelf' command,
which displays information about ELF files.
"""

import re

from memtab.models import Section
from memtab.parsers.base import MemtabGnuBinUtilsParser


class ReadElfSectionParser(MemtabGnuBinUtilsParser):
    """Parser for the output of the 'readelf' command.

    This class parses the output of the 'readelf' command to extract section
    information from ELF files.
    """

    command = "readelf"
    args = ["-SW"]  # need wide here too for x86 reasons

    def parse_output_into_results(self) -> None:
        """Parse the readelf output and populate the sections lists."""
        # Regex pattern to parse readelf -SW output lines
        # Handles section names with spaces (e.g., "P1 rw", "P1 zi", "P1 ui")
        # Format: [Nr] Name Type Addr Off Size ES Flg Lk Inf Al
        pattern = re.compile(
            r"^\s*\[\s*\d+\]\s+"  # [Nr] with optional whitespace
            r"(\S.*?)\s+"  # Name (non-greedy, can contain spaces)
            r"(\S+)\s+"  # Type
            r"([0-9a-fA-F]+)\s+"  # Addr
            r"([0-9a-fA-F]+)\s+"  # Off
            r"([0-9a-fA-F]+)\s+"  # Size
            r"([0-9a-fA-F]+)\s+"  # ES
            r"(\S*)"  # Flg (may be empty)
        )

        lines = self.raw_data.splitlines()
        for line in lines:
            if not line:
                continue
            # Skip header line
            if "[Nr]" in line:
                continue

            match = pattern.match(line)
            if match:
                name, section_type, addr, off, size_str, es, flags = match.groups()
                size = int(size_str, 16)
                if size:
                    self.result.sections.append(
                        Section(
                            name=name.strip(),
                            address=int(addr, 16),
                            size=size,
                            type=section_type,
                            flags=flags,
                        )
                    )
