# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""The base class from which all MemTab parsers should inherit."""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from memtab.models import ParserResult, Section, Symbol


class MemtabParser:
    """Base class for MemTab parsers.
    This class provides a common interface for all MemTab parsers.
    """

    def __init__(self, file: Path, cache: Optional[bool] = False, cache_dir: Optional[str] = None):
        """Initialize the MemTab parser."""
        if cache is not None:
            self.cache = cache
        if cache_dir is not None:
            self.cache_dir = cache_dir
        self.file = file
        self.__result = ParserResult()
        self.__command = ""
        self.prefix = ""
        self.__args: List[str] = []
        self.__tool_output = ""

    # region properties

    @property
    def file(self) -> Path:
        """Get the file being parsed.

        Returns:
            The file as a Path object.
        """
        return self.__file

    @file.setter
    def file(self, value: Path) -> None:
        """Set the file to be parsed.

        Args:
            value (Path): The file as a Path object.
        """
        if not isinstance(value, Path):
            raise TypeError("File must be a Path object.")
        if not value.exists():
            raise FileNotFoundError(f"File {value} does not exist.")
        self.__file = value

    @property
    def command(self) -> str:
        """Get the command used to run the tool.

        Returns:
            The command as a string.
        """
        return self.__command

    @command.setter
    def command(self, value: str) -> None:
        """Set the command to run the tool.

        Args:
            value (str): The command as a string.
        """
        self.__command = value

    @property
    def args(self) -> List[str]:
        """Get the arguments used for the tool command.

        Returns:
            The arguments as a string.
        """
        return self.__args

    @args.setter
    def args(self, value: List[str]) -> None:
        """Set the arguments for the tool command.

        Args:
            value (List[str]): The arguments as a list of strings.
        """
        if not isinstance(value, list):
            raise TypeError("Arguments must be a list of strings.")
        self.__args = value

    @property
    def raw_data(self) -> str:
        """Get the raw tool output.

        Returns:
            The raw output string from the tool.
        """
        return self.__tool_output

    @raw_data.setter
    def raw_data(self, value: str) -> None:
        """Set the raw tool output.

        Args:
            value (str): The raw output string from the tool.
        """
        if not isinstance(value, str):
            raise TypeError("Raw data must be a string.")
        self.__tool_output = value

    @property
    def result(self) -> ParserResult:
        """Get the complete parsing result.

        Returns:
            A ParserResult object containing sections, symbols and other data.
        """
        return self.__result

    @property
    def sections(self) -> List[Section]:
        """Get the parsed sections.

        Returns:
            A list of Section objects.
        """
        return self.result.sections

    @property
    def symbols(self) -> List[Symbol]:
        """Get the parsed symbols.

        Returns:
            A list of Symbol objects.
        """
        return self.result.symbols

    @property
    def cache(self) -> bool:
        """Check if caching is enabled.

        Returns:
            bool: True if caching is enabled, False otherwise.
        """
        return self.__cache

    @cache.setter
    def cache(self, value: bool) -> None:
        """Set whether to enable caching.

        Args:
            value (bool): True to enable caching, False to disable.
        """
        self.__cache = value

    @property
    def cache_dir(self) -> str:
        """Get the directory where cache files are stored.

        Returns:
            str: The path to the cache directory.
        """
        return self.__cache_dir

    @cache_dir.setter
    def cache_dir(self, value: str) -> None:
        """Set the directory where cache files are stored.

        Args:
            value (str): The path to the cache directory.
        """
        if not os.path.exists(value):
            os.makedirs(value)
        self.__cache_dir = value

    # endregion

    # region public methods
    def run(self) -> None:
        """Run the tool command and parse the output into results.

        This method executes the command specified in the `command` property,
        captures its output, and parses it into the `result` attribute.
        """
        self.run_system_command()
        self.parse_output_into_results()

    # endregion

    # region internal methods
    def parse_output_into_results(self) -> None:
        """Parse the tool output into the results attribute."""
        raise NotImplementedError("Subclasses must implement this method.")

    def run_system_command(self) -> None:
        """Run a system command and optionally cache the results."""

        def calculate_hash(command: List[str]) -> str:
            """calculate a hash on the input arguments, and, if there is an
                elf file in the input arguments, on that file itself.  Then,
                if we have something in our cache that matches the calculated hash,
                use that as our return value instead of re-running the command

            Args:
                command (List[str]): the command being executed

            Returns:
                str: the hash of the command
            """
            hash_md5 = hashlib.md5()
            for arg in command:
                hash_md5.update(arg.encode("utf-8"))
                if os.path.isfile(arg):
                    with open(arg, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
            return hash_md5.hexdigest()

        full_command = [f"{self.prefix}{self.command}"] + self.args + [str(self.file)]
        command_hash = calculate_hash(full_command)
        cache_file = os.path.join(self.__cache_dir, command_hash)
        if self.cache and os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                self.raw_data = f.read()
                return

        base_cmd = full_command[0]
        if shutil.which(base_cmd) is None:
            raise FileNotFoundError(f"{base_cmd} command not found - please check your gcc_prefix setting and your PATH variable.")
        result = subprocess.run(full_command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Command '{' '.join(full_command)}' failed with return code {result.returncode}.\n" f"Error: {result.stderr}")

        if self.cache:
            with open(cache_file, "w") as f:
                f.write(result.stdout)

        self.raw_data = result.stdout

    # endregion


class MemtabGnuBinUtilsParser(MemtabParser):
    """Base class for GNU Binutils parsers.

    This class provides a common interface for GNU Binutils parsers such as nm, objdump and readelf.
    The main extension this provides beyond the base MemtabParser is support for the GCC prefix attribute.
    """

    def __init__(self, file: Path, gcc_prefix: Optional[str], cache: Optional[bool] = False, cache_dir: Optional[str] = None):
        """Initialize the GNU Binutils parser."""
        super().__init__(file, cache, cache_dir)
        if gcc_prefix is not None:
            self.prefix = gcc_prefix
