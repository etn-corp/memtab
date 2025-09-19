# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""NM parser module for memtab.

This module provides parsing functionality for the output of the 'nm' command,
which lists symbols from object files.
"""

from typing import List, Optional, Tuple

from memtab.models import Symbol
from memtab.parsers.base import MemtabGnuBinUtilsParser

# Symbol type mapping from nm output
SYMBOL_TYPES = {
    "a": "absolute",  # esp32 has a lot of these
    "A": "absolute",
    "b": "bss",
    "B": "bss",
    "c": "common",
    "C": "common",
    "d": "data",
    "D": "data",
    "g": "group",
    "G": "group",
    "i": "indirect",
    "I": "indirect",
    "n": "note",
    "N": "debugging",
    "p": "stack",
    "r": "read-only",
    "R": "read-only",
    "s": "small",
    "S": "small",
    "t": "text",
    "T": "text",
    "u": "unique",
    "U": "undefined",
    "v": "weak",
    "V": "weak",
    "w": "weak",
    "W": "weak",
    "-": "stabs",
    "?": "unknown",
}


class NmParser(MemtabGnuBinUtilsParser):
    """Parser for the output of the 'nm' command.

    This class parses the output of the 'nm' command to extract symbol information
    such as address, size, type, and name.
    """

    command = "nm"
    args = ["-SlC"]

    def parse_output_into_results(self) -> None:
        """Parse the nm output and populate the symbols list."""
        for line in self.raw_data.split("\n"):
            if not line or not line[0].isnumeric():
                continue

            symbol = self._process_line(line)
            if symbol:
                self.result.symbols.append(symbol)

    # region parsing helper methods

    def _process_line(self, line: str) -> Optional[Symbol]:
        """Process a single line of nm output.

        Args:
            line: A line from the nm output.

        Returns:
            A Symbol object if parsing was successful, None otherwise.
        """
        # Get the address from the beginning of the line
        index_of_first_whitespace = line.find(" ")
        addr = int(line[0:index_of_first_whitespace], 16)  #  TODO - do we need to account for "thumb" addresses with a  `& ~0x0001`?

        # Extract size if available
        if line[index_of_first_whitespace + 1].isalpha() or line[index_of_first_whitespace + 1] == "?":
            size = 0
            type_index = index_of_first_whitespace + 1
        else:
            size_index = index_of_first_whitespace + 1
            size_end_index = line.find(" ", size_index)
            size = int(line[size_index:size_end_index].strip(), 16)
            type_index = size_end_index + 1

        def __extract_from_line(line: str, type_index: int) -> Symbol:
            # Parse the rest of the line
            line_remainder = line[type_index:]
            words = line_remainder.split()
            symbol_type = words[0].strip()
            symbol_name = ""
            symbol_file = ""
            symbol_line_number = 0

            # Extract symbol name and source file info
            if len(words) == 1:
                # Symbol with no source file
                symbol_name = words[0].strip()
            elif not line[-1].isdigit():
                symbol_name = " ".join(words[1:]).strip()
            elif any(x in words for x in ["guard", "variable", "for"]) or "::" in line or "operator" in words or "(" in line:
                # C++ symbol handling
                symbol_name, symbol_file, symbol_line_number = self._parse_cpp_symbol(line_remainder, words)
            else:
                symbol_name = words[1].strip()
                if len(words) == 3:
                    file_info = words[2].rsplit(":", 1)
                    symbol_file = file_info[0].strip()
                    try:
                        symbol_line_number = int(file_info[1])
                    except (IndexError, ValueError):
                        symbol_line_number = 0

            # Create and return the symbol
            return Symbol(
                name=symbol_name,
                address=addr,
                size=size,
                type=SYMBOL_TYPES.get(symbol_type, "unknown"),
                file=symbol_file,
                line_number=symbol_line_number,
            )

        return __extract_from_line(line, type_index)

    def _parse_cpp_symbol(self, line: str, words: List[str]) -> Tuple[str, str, int]:
        """Parse a C++ symbol line which can have complex formats.

        Args:
            line: The line text after the address and type.
            words: The split words from the line.

        Returns:
            A tuple of (symbol_name, file_path, line_number)
        """
        symbol_name = ""
        symbol_file = ""
        symbol_line_number = 0

        odd_tags = [".cc:", ".cpp:", ".h:", ".hpp:", ".tpp:", ".tcc:", "iostream:", "istream:"]
        if any(x in line for x in odd_tags):
            symbol_and_source = line.rsplit(None, 1)
            symbol_name = symbol_and_source[0][2:].strip()  # the 2: is to ignore symbol type
            location = symbol_and_source[1].rsplit(":", 1)
            symbol_file = location[0].strip()
            if ")" in symbol_file:
                symbol_file = ""
            else:
                try:
                    symbol_line_number = int(location[1])
                except (IndexError, ValueError):
                    symbol_line_number = 0
        else:
            symbol_name = " ".join(words[1:])

        return symbol_name, symbol_file, symbol_line_number

    # endregion
