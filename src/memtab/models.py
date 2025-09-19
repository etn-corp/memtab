# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Shared data models used across the memtab package.

This module defines the common data structures used by various parsers
and other components of the memtab package to ensure a consistent interface.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Symbol:
    """Represents a symbol in a binary.

    A symbol typically represents a function, variable, or other named entity
    in the compiled code.
    """

    name: str
    address: int
    size: int = 0
    type: str = ""
    file: str = ""
    line_number: int = 0
    region: str = ""  # e.g., "Flash", "Code", or "RAM"
    subregion: str = ""  # e.g., "Flash", "SRAM"
    elf_section: str = ""  # e.g., ".text", ".data", ".bss"
    commit: str = "unknown"  # git commit hash
    repo: str = ""  # git repository URL
    categories: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the symbol to a dictionary representation."""
        return {
            "symbol": self.name,
            "address": self.address,
            "size": self.size,
            "memory_type": self.type,
            "file": self.file,
            "line": self.line_number,
            "region": self.region,
            "subregion": self.subregion,
            "elf_section": self.elf_section,
            "categories": self.categories,
            "commit": self.commit,
            "repo": self.repo,
        }

    def __hash__(self) -> int:
        """Make the Symbol hashable.

        Uses a combination of name and address as these should uniquely identify a symbol.
        """
        return hash((self.name, self.address))

    def __eq__(self, other: object) -> bool:
        """Equality comparison for Symbol objects.

        Two symbols are considered equal if they have the same name and address.
        """
        if not isinstance(other, Symbol):
            return NotImplemented
        return self.name == other.name and self.address == other.address


@dataclass
class Section:
    """Represents a section in a binary.

    A section is a segment of the binary that contains code or data with
    specific properties (e.g., read-only, executable).
    """

    name: str
    address: int
    size: int
    flags: str = ""
    type: str = ""
    calculated_symbol_size: int = 0  # convenience field
    unused: int = 0  # convenience field for unused space in the section


@dataclass
class Region:
    """Represents a memory region in the target system.

    A memory region is a contiguous block of physical memory
    with specific properties (e.g., flash, RAM).
    """

    name: str
    start: int
    end: int
    spare: int
    size: int = 0
    flags: str = ""
    region: str = ""  # "Flash", "Code" or "RAM"

    def __post_init__(self) -> None:
        if self.size == 0 and self.end > self.start:
            self.size = self.end - self.start + 1


@dataclass
class SubRegion:
    """Represents a sub-region of a memory region.

    A sub-region is a segment of a memory region with specific properties,
    such as flash, RAM, etc.
    """

    name: str
    start: int
    end: int
    size: int = 0
    parent_region: str = ""

    def __post_init__(self) -> None:
        if self.size == 0 and self.end > self.start:
            self.size = self.end - self.start + 1


@dataclass
class MemtabCategory:
    """Name and subcategories for a symbol.  This is used to categorize symbols"""

    name: str = ""
    categories: List["MemtabCategory"] = field(default_factory=list)


@dataclass
class MemtabSourceCode:
    """Details about source code"""

    categories: List[Dict[str, MemtabCategory]] = field(default_factory=list)
    root: str = ""


@dataclass
class MemtabCPU:
    """Details about the CPU.  This is used to categorize symbols"""

    memory_regions: List[Region] = field(default_factory=list)
    gcc_prefix: str = ""
    name: str = ""

    def __bool__(self) -> bool:
        return bool(self.memory_regions) or bool(self.gcc_prefix) or bool(self.name)


@dataclass
class MemtabConfig:
    """Configuration for the memory tabulator"""

    Project: str = ""
    CPU: MemtabCPU = field(default_factory=MemtabCPU)
    SourceCode: MemtabSourceCode = field(default_factory=MemtabSourceCode)

    def asdict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        from dataclasses import asdict

        return_dict = asdict(self)
        return_dict["Source Code"] = return_dict.pop("SourceCode", {})
        cpu = return_dict.get("CPU", {})
        if cpu and "memory_regions" in cpu:
            memory_regions = cpu.pop("memory_regions")
            cpu["memory regions"] = [
                {"Flash": [region for region in memory_regions if region["region"] == "Code" or region["region"] == "Flash"]},
                {"RAM": [region for region in memory_regions if region["region"] == "RAM"]},
            ]

        return return_dict


@dataclass
class ParserResult:
    """Common result structure for all parsers.

    This provides a consistent interface for Memtab to process parsing results
    from different sources.
    """

    sections: List[Section] = field(default_factory=list)
    symbols: List[Symbol] = field(default_factory=list)
    regions: List[Region] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
