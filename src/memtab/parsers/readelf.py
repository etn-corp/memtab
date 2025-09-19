# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""ReadElf parser module for memtab.

This module provides parsing functionality for the output of the 'readelf' command,
which displays information about ELF files.
"""

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
        lines = self.raw_data.splitlines()
        for line in lines:
            if not line:
                continue
            # '  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al'
            if line.startswith("  [") and "[Nr]" not in line:
                line = line.replace("[", "").replace("]", "")
                words = line.split()
                size = int(words[5], 16)
                if size:
                    self.result.sections.append(
                        Section(
                            name=words[1],
                            address=int(words[3], 16),
                            size=size,
                            type=words[2],
                            flags=words[7],
                        )
                    )
