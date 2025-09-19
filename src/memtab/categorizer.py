# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Category assignment module for memtab.

This module provides functionality to assign categories to symbols from various
sources (nm, readelf, objdump, map files) in a consistent manner.
"""

import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Dict, List, Optional

from memtab.models import Region, Section, Symbol


def normalize_symbol_file_path(file_path: str, comp_dir: Optional[str] = None) -> str:
    """Normalize a symbol file path.

    This function normalizes file paths from different sources to ensure
    consistent category assignment.

    Args:
        file_path: The file path to normalize.
        comp_dir: The compilation directory to use as a reference.

    Returns:
        A normalized file path.
    """
    if not file_path:
        return ""

    # Handle Unix and Windows paths
    if "/" in file_path or "\\" in file_path:
        try:
            # Try Windows path normalization
            if "\\" in file_path:
                norm_path = str(PureWindowsPath(file_path).as_posix())
            else:
                norm_path = str(PurePosixPath(file_path))

            # Remove compilation directory prefix if provided
            if comp_dir and norm_path.startswith(comp_dir):
                norm_path = norm_path[len(comp_dir) :]
                if norm_path.startswith("/"):
                    norm_path = norm_path[1:]

            return norm_path
        except Exception:
            pass
    return file_path


def categorize_symbol(symbol: Symbol, categories: List[Dict[str, Any]], comp_dir: Optional[str] = None) -> List[str]:
    """Categorize a symbol based on its name and file path.

    This function takes a symbol and attempts to categorize it based on
    the provided categories configuration.

    Args:
        symbol: The symbol to categorize.
        categories: A list of category dictionaries with names and patterns.
        comp_dir: The compilation directory, to help normalize paths.

    Returns:
        A list of category names that the symbol belongs to.
    """
    normalized_file = normalize_symbol_file_path(symbol.file, comp_dir)
    return _categorize_symbol_list(symbol.name, normalized_file, categories)


def _categorize_symbol_list(name: str, file_path: str, categories: List[Dict[str, Any]]) -> List[str]:
    """Process a list of categories to find matches for a symbol.

    Args:
        name: The symbol name.
        file_path: The normalized file path.
        categories: A list of categories to check against.

    Returns:
        A list of category names the symbol belongs to.
    """
    symbol_category: List[str] = []

    for category in categories:
        updated_results = _categorize_symbol_dict(name, file_path, category)
        if updated_results:
            cat_name = category["name"]
            symbol_category.extend(updated_results)
            if cat_name not in symbol_category:
                symbol_category.append(cat_name)
            break

    return symbol_category


def _categorize_symbol_dict(name: str, file_path: str, category_dict: Dict[str, Any]) -> List[str]:
    """Check if a symbol matches the patterns in a category dictionary.

    Args:
        name: The symbol name.
        file_path: The normalized file path.
        category_dict: The category dictionary with patterns and subcategories.

    Returns:
        A list of category names the symbol belongs to.
    """
    return_symbol_category: List[str] = []
    compare = ["patterns", "regexes", "files", "directories", "symbols"]

    if any(x in category_dict for x in compare):
        if _process_subcategory(name, file_path, category_dict):
            return_symbol_category.append(category_dict["name"])
    elif "categories" in category_dict:
        return_symbol_category.extend(_categorize_symbol_list(name, file_path, category_dict["categories"]))

    return return_symbol_category


def _process_subcategory(name: str, file_path: str, category: Dict[str, Any]) -> bool:
    """Process a subcategory definition to see if the symbol matches.

    Args:
        name: The symbol name.
        file_path: The normalized file path.
        category: The category dictionary to check against.

    Returns:
        True if the symbol matches this category, False otherwise.
    """
    patterns = category.get("patterns", [])
    regexes = category.get("regexes", [])

    if patterns or regexes:
        return _pattern_and_regex_search(patterns, regexes, name, file_path)
    else:
        return _file_directory_symbol_search(category, name, file_path)


def _pattern_and_regex_search(patterns: List[str], regexes: List[str], name: str, file_path: str) -> bool:
    """Search for patterns and regexes in the symbol name and file path.

    Args:
        patterns: List of simple string patterns to search for.
        regexes: List of regular expressions to search for.
        name: The symbol name.
        file_path: The normalized file path.

    Returns:
        True if any pattern or regex matches, False otherwise.
    """
    for pattern in patterns:
        if pattern in name or (file_path and pattern in file_path):
            return True

    for regex in regexes:
        try:
            if re.search(regex, name) or (file_path and re.search(regex, file_path)):
                return True
        except re.error:
            # Skip invalid regexes
            continue

    return False


def _file_directory_symbol_search(category: Dict[str, Any], name: str, file_path: str) -> bool:
    """Check if a symbol belongs to specific files, directories, or symbol lists.

    Args:
        category: The category dictionary with file/directory/symbol specifications.
        name: The symbol name.
        file_path: The normalized file path.

    Returns:
        True if the symbol belongs to this category, False otherwise.
    """
    files = category.get("files", [])
    directories = category.get("directories", [])
    symbols = category.get("symbols", [])

    def check_files_list(files: List[str], file_path: str) -> bool:
        if files and file_path:
            for f in files:
                if file_path.endswith(f):
                    return True
        return False

    def check_directories_list(directories: List[str], file_path: str) -> bool:
        if directories and file_path:
            for d in directories:
                if "/" + d + "/" in file_path:
                    return True
        return False

    def check_symbols_list(symbols: List[str]) -> bool:
        return name in symbols

    if isinstance(files, list):
        check_files_result = check_files_list(files, file_path)
    else:
        check_files_result = _process_subcategory(name, file_path, files)
    if isinstance(directories, list):
        check_directories_result = check_directories_list(directories, file_path)
    else:
        check_directories_result = _process_subcategory(name, file_path, directories)
    if isinstance(symbols, list):
        check_symbols_result = check_symbols_list(symbols)
    else:
        check_symbols_result = _process_subcategory(name, file_path, symbols)

    return check_files_result or check_directories_result or check_symbols_result


def assign_addr_to_region(addr: int, memory_regions: List[Region]) -> Optional[Region]:
    """Assign a memory region to an address based on its range.

    Args:
        addr: The address to assign a region to.
        memory_regions: List of memory regions to check against.

    Returns:
        The matching memory region if found, otherwise None.
    """
    for region in memory_regions:
        if region.start <= addr <= region.end:
            return region
    return None


def assign_symbol_to_region(symbol: Symbol, memory_regions: List[Region]) -> Optional[Region]:
    """Assign a memory region to a symbol based on its address."""
    return assign_addr_to_region(symbol.address, memory_regions)


def assign_symbols_to_regions(symbols: List[Symbol], regions: List[Region]) -> None:
    """Assign symbols to memory regions based on address ranges.

    Args:
        symbols: List of symbols to assign regions to.
        regions: List of memory regions to match against.
    """
    for symbol in symbols:
        assigned_region = assign_symbol_to_region(symbol, regions)
        if assigned_region:
            symbol.region = assigned_region.name
            break


def assign_symbols_to_sections(symbols: List[Symbol], sections: List[Section]) -> None:
    """Assign symbols to sections based on address ranges.

    Args:
        symbols: List of symbols to assign sections to.
        sections: List of sections to match against.
    """
    for symbol in symbols:
        for section in sections:
            if section.address <= symbol.address < section.address + section.size:
                symbol.elf_section = section.name
                break
