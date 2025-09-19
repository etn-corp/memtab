# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Size parser module for memtab.

This module provides parsing functionality for the output of the 'size' command,
which lists section sizes and the total size of a binary file.
"""

from pathlib import Path
from typing import Dict, Optional

from memtab.models import Section
from memtab.parsers.base import MemtabGnuBinUtilsParser


class SizeParser(MemtabGnuBinUtilsParser):
    """Parser for the output of the 'size' command.

    This class parses the output of the 'size' command to extract section sizes
    from binary files.
    """

    command = "size"

    def __init__(self, file: Path, gcc_prefix: Optional[str], cache: Optional[bool] = False, cache_dir: Optional[str] = None) -> None:
        """Initialize the parser with instance-specific attributes.

        All arguments are passed directly to the parent class.
        """
        super().__init__(file, gcc_prefix, cache, cache_dir)
        self.section_sizes: Dict[str, int] = {}
        self.total_size: int = 0

    def parse_output_into_results(self) -> None:
        """Parse the size output and extract section sizes."""
        lines = self.raw_data.strip().split("\n")

        # Skip the header line if it exists
        start_line = 1 if "text" in lines[0].lower() and "data" in lines[0].lower() else 0

        # Process each size line
        for line in lines[start_line:]:
            parts = line.split()
            if len(parts) >= 4:  # text, data, bss, dec, hex
                try:
                    text_size = int(parts[0])
                    data_size = int(parts[1])
                    bss_size = int(parts[2])
                    dec_size = int(parts[3])

                    self.section_sizes[".text"] = text_size
                    self.section_sizes[".data"] = data_size
                    self.section_sizes[".bss"] = bss_size
                    self.total_size = dec_size

                    # Add sections to the common result structure
                    self.result.sections.append(
                        Section(
                            name=".text",
                            address=0,  # Size command doesn't provide addresses
                            size=text_size,
                        )
                    )

                    self.result.sections.append(Section(name=".data", address=0, size=data_size))

                    self.result.sections.append(Section(name=".bss", address=0, size=bss_size))

                    # Add metadata
                    self.result.metadata["total_size"] = dec_size

                except (ValueError, IndexError):
                    # Skip lines that don't match the expected format
                    continue

    def get_total_size(self) -> int:
        """Get the total size of the binary.

        Returns:
            The total size in bytes.
        """
        return self.total_size
