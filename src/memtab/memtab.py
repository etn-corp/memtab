# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""The main class for the memory tabulator.

This class is intended to be called from other Python code. The cli.py
provides a convenient entry point to get to this from the command line,
but you could also script a call to this class directly from your own Python code.
"""

import datetime
import hashlib
import json
import logging
import os
import shutil
import warnings
from importlib.metadata import version
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import yaml
from appdirs import user_cache_dir
from elftools.elf.elffile import ELFFile
from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from jsonschema import Draft7Validator as draftValidator
from jsonschema import validate
from pandas import DataFrame
from referencing import Registry
from referencing.jsonschema import DRAFT7

from memtab.categorizer import categorize_symbol
from memtab.models import (
    MemtabConfig,
    MemtabCPU,
    MemtabSourceCode,
    ParserResult,
    Region,
    Section,
    Symbol,
)
from memtab.parsers.base import MemtabParser
from memtab.parsers.map import MapFileParser
from memtab.parsers.nm import NmParser
from memtab.parsers.objdump import ObjDumpParser
from memtab.parsers.readelf import ReadElfSectionParser
from memtab.parsers.size import SizeParser

pd.options.mode.copy_on_write = True


class Memtab:
    """The primary class for the memory tabulator.

    This class is responsible for coordinating the parsing of various data sources
    (nm, readelf, objdump, size, map files), processing the output to produce a list
    of symbols and their associated memory regions, and categorizing them consistently.
    """

    def __init__(
        self,
        elf: Optional[Path] = None,
        map_file: Optional[Path] = None,
        config: List[Path] = [],
        project: Optional[str] = None,
        cache: bool = True,
        check: bool = False,
        debug: bool = False,
    ):
        """Initialize the memory tabulator.

        Args:
            elf (Path, optional): The ELF file to parse.
            map_file (Path, optional): The map file to parse.
            config (List[Path]): The config file(s).
            cache (bool, optional): Use cache if it exists, create cache if it doesn't. Defaults to False.
            check (bool, optional): Sanity check against other binutils outputs. Defaults to False.
            debug (bool, optional): Create debug artifacts like excel. Defaults to False.
        """

        self.cache = cache
        self.__cache_dir = user_cache_dir("memtab", "memtab")
        self.__elf: Optional[Path] = None
        self.check = check
        self.debug = debug

        self.symbols: DataFrame  # individual symbols
        self.regions: DataFrame  # ranges of memory, given human readable titles
        self.sections: DataFrame  # per the ELF standard, things like text, data, bss, etc.
        self.build_metadata: Dict[str, Union[int, str]] = {}
        self.elf_metadata: Dict[str, Union[int, str]] = {}
        self.__commit_metadata: Dict[str, Dict[str, str]] = {}
        self.__config: MemtabConfig = MemtabConfig(CPU=MemtabCPU(), SourceCode=MemtabSourceCode())
        self.__config_files = config
        if cache:
            os.makedirs(self.__cache_dir, exist_ok=True)
        self.__schema_dir = os.path.join(os.path.dirname(__file__), "schemas")
        self.__output_schema_path = os.path.join(self.__schema_dir, "memtab_schema.json")
        with open(self.__output_schema_path, "r") as stream:
            self.__output_schema = json.load(stream)
        self.__config_schema_path = os.path.join(self.__schema_dir, "memtab_config_schema.json")
        with open(self.__config_schema_path, "r") as stream:
            self.__config_schema = json.load(stream)

        self.__config_file_schema_path = os.path.join(self.__schema_dir, "memtab_config_file_schema.json")
        with open(self.__config_file_schema_path, "r") as stream:
            self.__config_file_schema = json.load(stream)

            self.__config_registry = Registry().with_resources([("urn:memtab-config-file", DRAFT7.create_resource(self.__config_file_schema))])

        if not elf:
            elf = Path(os.path.join(os.getcwd(), "zephyr.elf"))

        self.elf = elf
        self.cfg_found = False
        self.__process_configs(config, project)
        self.__process_env()
        self.map = None
        if map_file:
            self.map = map_file

    def __process_env(self) -> None:
        """Read environment variables for build metadata."""
        # Detect if running inside a GitHub Actions workflow
        if "GITHUB_ACTIONS" in os.environ and os.environ["GITHUB_ACTIONS"] == "true":
            repo_name = os.environ["GITHUB_REPOSITORY"]
            repo_words = repo_name.split("/")
            owner = repo_words[0]
            repository = repo_words[1]
            sha = os.environ["GITHUB_SHA"]
            build_type = os.environ["GITHUB_EVENT_NAME"]
            branch = os.environ["GITHUB_REF"]
            run_id = int(os.environ["GITHUB_RUN_ID"])
            attempt_id = int(os.environ["GITHUB_RUN_ATTEMPT"])
            workflow_name = os.environ["GITHUB_WORKFLOW"]
            html_url = f"https://github.com/{repo_name}/actions/runs/{run_id}"
        else:
            # Try to get the repository info from git
            try:
                repo = Repo(self.__config_files[0], search_parent_directories=True)
                origin_repo_url = str(repo.remotes[0].url) if repo.remotes else "unknown"
                sha = str(repo.head.commit.hexsha)
                branch = str(repo.active_branch.name) if not repo.head.is_detached else "detached"
                owner, repository = origin_repo_url.split("/")[-2:]
                repository = repository.replace(".git", "")
            except (NoSuchPathError, InvalidGitRepositoryError, IndexError, ValueError):
                sha = "ffffffffffffffffffffffffffffffffffffffff"
                branch = "unknown"
                owner = "unknown"
                repository = "unknown"
            build_type = "unknown"
            run_id = 0
            attempt_id = 0
            workflow_name = "unknown"
            html_url = "unknown"

        self.build_metadata = {
            "repository_name": repository,
            "owner": owner,
            "commit_sha": sha,
            "build_id": run_id,
            "attempt_id": attempt_id,
            "name": workflow_name,
            "repository_url": html_url,
            "type": build_type,
            "branch": branch,
        }

    @staticmethod
    def __create_memory_regions(region_type: str, memory_regions: List[Dict[str, Any]]) -> List[Region]:
        region_list: List[Region] = []
        for memory_region in memory_regions:
            name = memory_region["name"]
            start = int(memory_region["start"], 16)
            if "end" in memory_region:
                end = int(memory_region["end"], 16)
            else:
                end = start + int(memory_region["size"], 16)

            region = Region(name, start, end, end - start, region=region_type)
            region_list.append(region)
        return region_list

    def __create_default_config(self) -> None:
        """we likely were passed a default config file. let's warn that it was not found, but then proceed with default values"""
        self.config.CPU = MemtabCPU()
        logging.info("No config file found. Using default values.")
        if self.elf:
            # first we need to determine the gcc prefix from the elf file format
            with open(self.elf, "rb") as f:
                elf = ELFFile(f)
                self.config.CPU.gcc_prefix = ""
                if elf.get_machine_arch() == "ARM":
                    # in the case of arm, we could be building w/ zephyr, so we need to see
                    # if we have arm-none-eabi binutils on the PATH, or arm-zephyr-eabi.
                    self.config.CPU.gcc_prefix = "arm-none-eabi-"
                    if not shutil.which(self.config.CPU.gcc_prefix + "gcc"):
                        self.config.CPU.gcc_prefix = "arm-zephyr-eabi-"
                        if not shutil.which(self.config.CPU.gcc_prefix + "gcc"):
                            logging.warning("No arm-none-eabi or arm-zephyr-eabi found on PATH.  Using default. Expect errors in output ($d and $t symbols)")
                            self.config.CPU.gcc_prefix = ""
                elif elf.get_machine_arch() == "x86":
                    pass  # ok for now
                else:
                    raise ValueError(f"Unknown architecture: {elf.get_machine_arch()}")

        # we can preload categories with unknown/unknown
        self.config.SourceCode = MemtabSourceCode(root="unknown")
        self.config.SourceCode.categories = []

        # and we can preload regions with some default values based on the
        # processor type.  it is likely this is incorrect or incomplete, but
        # its a starting point, and can be expanded over time.
        flash = [{"name": "flash", "start": "0x08000000", "size": "0x10000"}]
        ram = [{"name": "ram", "start": "0x20000000", "size": "0x10000"}]

        self.config.CPU.memory_regions.extend(self.__create_memory_regions("Flash", flash))
        self.config.CPU.memory_regions.extend(self.__create_memory_regions("RAM", ram))
        self.config.Project = "unknown"

    def __process_config(self, config: Path, project: Optional[str] = None) -> None:
        """read the YAML file into internal memory"""
        if not config or not os.path.exists(config):
            return

        self.cfg_found = True
        with open(config, "r") as stream:
            config_data = yaml.safe_load(stream)

        validator = draftValidator(self.__config_file_schema, registry=self.__config_registry)
        validator.validate(config_data)

        self.__process_cpu_config(config_data)
        self.__process_source_code_config(config_data)
        self.__process_project_config(config_data, project)
        self.__process_elf_config(config_data, config)
        self.__process_includes(config_data, config)

    def __process_cpu_config(self, config_data: Dict[str, Any]) -> None:
        """Process CPU-related configuration."""
        if "CPU" in config_data:
            if self.config.CPU is not None and self.config.CPU:
                logging.warning("CPU config already set. Overriding with new values.")
            cpu = MemtabCPU()
            cpu_config = config_data["CPU"]
            if "gcc_prefix" in cpu_config:
                cpu.gcc_prefix = cpu_config["gcc_prefix"]
            if "name" in cpu_config:
                cpu.name = cpu_config["name"]

            if "memory regions" in cpu_config:
                for region in cpu_config["memory regions"]:
                    if "Code" in region:
                        warnings.warn(
                            "The 'Code' region is deprecated. Please use 'Flash' instead. This will be removed in a future version.",
                            DeprecationWarning,
                        )
                        cpu.memory_regions.extend(self.__create_memory_regions("Flash", region["Code"]))
                    if "Flash" in region:
                        cpu.memory_regions.extend(self.__create_memory_regions("Flash", region["Flash"]))
                    if "RAM" in region:
                        cpu.memory_regions.extend(self.__create_memory_regions("RAM", region["RAM"]))
            self.config.CPU = cpu

    def __process_source_code_config(self, config_data: Dict[str, Any]) -> None:
        """Process source code-related configuration."""
        if "Source Code" in config_data:
            source_code_config = config_data["Source Code"]
            self.config.SourceCode = MemtabSourceCode(source_code_config["categories"], source_code_config["root"])

    def __process_project_config(self, config_data: Dict[str, Any], project: Optional[str]) -> None:
        """Process project-related configuration."""
        if "Project" in config_data:
            if self.config.Project is not None and len(self.config.Project):
                logging.warning(f"Project config already set. Overriding {self.config.Project} with {config_data['Project']}.")
            self.config.Project = config_data["Project"]
        if project:
            if self.config.Project is not None and len(self.config.Project):
                logging.warning(f"Project config already set. Overriding {self.config.Project} with {project}.")
            self.config.Project = project

    def __process_elf_config(self, config_data: Dict[str, Any], config_path: Path) -> None:
        """Process ELF-related configuration."""
        if "ELF" in config_data:
            elf_path = config_data["ELF"]
            resolved_elf_path = Path(config_path).parent / elf_path
            resolved_elf_path = resolved_elf_path.resolve()
            if resolved_elf_path.exists():
                if self.elf and Path(self.elf) != resolved_elf_path:
                    raise ValueError(f"ELF file already set to {self.elf}. Cannot override with {resolved_elf_path} from config.")
                self.elf = resolved_elf_path
            else:
                logging.warning(f"ELF file {resolved_elf_path} specified in config not found.")

    def __process_includes(self, config_data: Dict[str, Any], parent_config_path: Path) -> None:
        """Process included configuration files, resolving paths relative to the parent config file."""
        if "include" in config_data:
            for include in config_data["include"]:
                include_path = Path(include)
                if include_path.is_absolute():
                    resolved_include = include_path
                else:
                    resolved_include = Path(parent_config_path).parent / include_path
                if not resolved_include.exists():
                    logging.warning(f"Included config file '{resolved_include}' specified in '{parent_config_path}' not found.")
                    continue
                self.__process_config(resolved_include)

    def __process_configs(self, config_files: List[Path], project: Optional[str]) -> None:
        """read the YAML file into internal memory

        Args:
            config_files (List[Path]): the path(s) to the YAML file(s) to be read
            project (Optional[str]): the project name
        """
        if config_files:
            for config in config_files:
                self.__process_config(config, project=project)
        if not self.cfg_found:
            self.__create_default_config()
        validator = draftValidator(self.__config_schema, registry=self.__config_registry)

        # now that we're through all files we can check that we got everything we need from at least ONE of the provided configurations.
        # throughout we were validating individual files, but they may not have had the complete picture, like we do at this point.
        config_dict = self.config.asdict()
        validator.validate(config_dict)

    def clean_cache(self) -> None:
        if os.path.exists(self.__cache_dir):
            for file in os.listdir(self.__cache_dir):
                os.remove(os.path.join(self.__cache_dir, file))

    def tabulate(self) -> DataFrame:
        """Main entry point for the memory tabulator.

        This method coordinates the parsing of data from various sources,
        processes symbols, assigns categories, and produces the final output.

        Returns:
            A dictionary containing the tabulated memory data.
        """
        if not self.elf:
            raise ValueError("No ELF file provided. Please set the 'elf' property before calling tabulate().")
        self.__parsers: List[MemtabParser] = [
            NmParser(file=self.elf, gcc_prefix=self.config.CPU.gcc_prefix, cache=self.cache, cache_dir=self.__cache_dir),
            ReadElfSectionParser(file=self.elf, gcc_prefix=self.config.CPU.gcc_prefix, cache=self.cache, cache_dir=self.__cache_dir),
            SizeParser(file=self.elf, gcc_prefix=self.config.CPU.gcc_prefix, cache=self.cache, cache_dir=self.__cache_dir),
            ObjDumpParser(file=self.elf, gcc_prefix=self.config.CPU.gcc_prefix, cache=self.cache, cache_dir=self.__cache_dir),
        ]
        if self.map:
            self.__parsers.append(MapFileParser(self.map))

        self.__tool_results: Dict[str, ParserResult] = {}

        for parser in self.__parsers:
            parser.run()
            self.__tool_results[parser.command] = parser.result

        merged_result = self.__merge_results(self.__tool_results)

        # Process the parsed data
        self.__create_symbols_dataframe(merged_result.symbols)
        self.__process_sections(merged_result.sections)

        self.__assign_assigned_size()

        # Assign regions to symbols
        self.__assign_regions_to_symbols()

        self.__calculate_metadata_for_regions()

        # Assign sections to symbols based on addresses
        self.__assign_sections_to_symbols(merged_result.sections)

        # Apply category assignments after all data is processed
        self.__categorize_symbols()

        # Perform sanity checks if requested
        if self.check:
            self.__sanity_check()

        # Generate the final output
        return self.symbols

    def __create_symbols_dataframe(self, symbols: List[Symbol]) -> None:
        """Convert the list of symbols into a pandas dataframe."""
        symbols_data = [symbol.to_dict() for symbol in symbols]
        df = pd.DataFrame(symbols_data)

        df = df[df["size"] != 0]  # remove zero-sized elements

        # Remove symbols where the address value is the duplicate of address in another row
        # AND size is duplicate of size in another row (keep the first occurrence)
        df = df[~df.duplicated(subset=["address", "size"], keep="first")]

        df.set_index("address", inplace=True)
        df.sort_index(inplace=True)

        # lets filter out repeated items
        df = df[~df.index.duplicated(keep="first")]

        self.symbols = df

    def __assign_assigned_size(self) -> None:
        """Use the spacing between one symbol and the next, in addition to that symbol's size, to calculate the assigned size of each symbol."""

        # Calculate assigned sizes
        self.symbols["assigned_size"] = 0
        for i in range(len(self.symbols) - 1):
            current_addr = self.symbols.index[i]
            next_addr = self.symbols.index[i + 1]
            self.symbols.at[current_addr, "assigned_size"] = next_addr - current_addr

        # Handle the last symbol
        if len(self.symbols) > 0:
            last_addr = self.symbols.index[-1]
            self.symbols.at[last_addr, "assigned_size"] = self.symbols.loc[last_addr, "size"]

        # Check for consistency between size and assigned size
        # If assigned_size < size, it means our calculation is wrong
        size_inconsistencies = self.symbols[self.symbols["assigned_size"] < self.symbols["size"]]
        if not size_inconsistencies.empty:
            # Log inconsistencies between size and assigned_size
            for addr, row in size_inconsistencies.iterrows():
                logging.debug(f"Size inconsistency: symbol={row['symbol']}, address=0x{addr:x}, size={row['size']}, assigned_size={row['assigned_size']}")

    def __process_sections(self, sections: List[Section]) -> None:
        """Process the sections from readelf output."""
        sections_data = []
        for section in sections:
            sections_data.append(
                {
                    "name": section.name,
                    "address": section.address,
                    "size": section.size,
                    "flags": section.flags,
                    "type": getattr(section, "type", ""),
                    "calculated_symbol_size": section.calculated_symbol_size,
                    "unused": section.unused,
                }
            )

        df = pd.DataFrame(sections_data)
        if len(df) > 0:
            # Filter out unwanted sections
            debug_keywords = ["debug", "ARM", "eh_frame", "dynsym", "comment"]
            debug_mask = df["name"].apply(lambda x: any(keyword in x for keyword in debug_keywords))
            df = df.loc[~debug_mask]

            # Remove table sections
            if "type" in df.columns:
                type_mask = df["type"].str.contains("TAB", na=False)
                df = df.loc[~type_mask]

            zero_mask = (df["address"] != 0) & (df["size"] != 0)
            df = df.loc[zero_mask]

        self.sections = df

    def __calculate_metadata_for_regions(self) -> None:
        """Calculate memory region spares, based on the symbol data that has been made so far."""
        self.regions = DataFrame(self.config.CPU.memory_regions)

        for region_idx, region in self.regions.iterrows():
            region_symbols = self.symbols[(self.symbols.index >= region["start"]) & (self.symbols.index <= region["end"])]
            region_size = region_symbols["size"].sum()
            self.regions.loc[region_idx, "spare"] -= region_size

            if self.regions.loc[region_idx, "spare"] < 0:
                raise ValueError(f"Spare memory for region {region['name']} went below ({self.regions.loc[region_idx, 'spare']})")
        # get the lowest from self.regions where the region is RAM
        self.lowest_RAM_addr = self.regions[self.regions["region"] == "RAM"]["start"].min()

    def __assign_regions_to_symbols(self) -> None:
        """Assign memory regions to symbols based on their addresses."""
        for idx, _ in self.symbols.iterrows():
            region, subregion = self.__get_region_for_address(idx)
            self.symbols.at[idx, "region"] = region
            self.symbols.at[idx, "subregion"] = subregion

    def __get_region_for_address(self, addr: int) -> Tuple[str, str]:
        """Get the region and subregion for a given address."""
        for region in self.__config.CPU.memory_regions:
            if region.start <= addr <= region.end:
                return region.region, region.name
        return "unknown", "unknown"

    def __assign_sections_to_symbols(self, sections: List[Section]) -> None:
        """Assign sections to symbols based on their addresses."""
        for section in sections:
            section_start = section.address
            section_end = section.address + section.size

            # Find symbols within this section's address range
            section_addr_filter = (self.symbols.index >= section_start) & (self.symbols.index < section_end)
            self.symbols.loc[section_addr_filter, "elf_section"] = section.name

            # now lets do some further updating of the section list based on what we found in the symbols
            section_symbols = self.symbols[section_addr_filter]
            if section_symbols.empty:
                continue
            else:
                # really all that needs to be done here is to adjust the last symbol's assigned size to cut off
                # at the end of the section, instead of (potentially) reaching into the next section
                last_symbol_address = section_symbols.index[-1]
                self.symbols.at[last_symbol_address, "assigned_size"] = section_end - last_symbol_address

                # now reset section symbols
                section_symbols = self.symbols[section_addr_filter]

                section_assigned_size = section_symbols["assigned_size"].sum()
                self.sections.loc[self.sections.name == section.name, "calculated_symbol_size"] = section_assigned_size

                self.sections.loc[self.sections.name == section.name, "unused"] = min(section_symbols.index) - section.address

    def __categorize_symbols(self) -> None:
        """Categorize symbols based on configured patterns."""
        if not self.__config.SourceCode.categories:
            return

        # Apply categorization to each symbol
        categories = self.__config.SourceCode.categories
        for idx, row in self.symbols.iterrows():
            symbol_categories = categorize_symbol(
                Symbol(name=row["symbol"], address=idx, file=row["file"], size=row["size"], type=row["memory_type"]),
                categories,
                self.__config.SourceCode.root,
            )

            if not symbol_categories:
                symbol_categories = ["unknown"]

            symbol_categories.reverse()

            symbol_categories_as_dict = {str(i): category for i, category in enumerate(symbol_categories)}

            try:
                self.symbols.at[idx, "categories"] = symbol_categories_as_dict
            except ValueError:
                logging.warning(f"Failed to update categories for symbol at address {idx}. ")

    def __sanity_check(self) -> None:
        """Perform sanity checks against other binutils outputs."""
        # Compare with size command output
        size_result = self.__tool_results["size"]

        # Compare section sizes
        for section in size_result.sections:
            matching_sections = self.sections[self.sections["name"] == section.name]
            if not matching_sections.empty:
                calculated_size = matching_sections["size"].sum()
                if calculated_size != section.size:
                    logging.warning(f"Section {section.name} size mismatch: {calculated_size} vs {section.size}")

        # Additional sanity checks as needed

    @property
    def debug(self) -> bool:
        """Get or set the debug flag."""
        return self.__debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self.__debug = value

    @property
    def cache(self) -> bool:
        """Get or set the cache flag."""
        return self.__caching

    @cache.setter
    def cache(self, value: bool) -> None:
        self.__caching = value

    @property
    def check(self) -> bool:
        """Get or set the check flag."""
        return self.__check

    @check.setter
    def check(self, value: bool) -> None:
        self.__check = value

    @property
    def schema(self) -> Any:
        """Returns the schema file for the output data format."""
        return self.__output_schema

    @property
    def config(self) -> MemtabConfig:
        """Returns the config data"""
        return self.__config

    @config.setter
    def config(self, value: MemtabConfig) -> None:
        self.__config = value

    @property
    def project(self) -> str:
        """The project name"""
        return self.config.Project

    @project.setter
    def project(self, value: str) -> None:
        self.config.Project = value

    @property
    def memtab(self) -> Dict[str, Any]:
        """The Memory Table. Contains version, symbols array, regions array, and metadata (i.e. where the memory table came from/when it was produced)"""
        memory_table = {
            "schema_version": self.__output_schema["properties"]["schema_version"]["const"],
            "project": self.project,
            "symbols": self.symbols.reset_index().to_dict("records"),
            "regions": self.regions.to_dict("records"),
            "elf_sections": self.sections.to_dict("records"),
            "metadata": self.elf_metadata,
            "build": self.build_metadata,
        }

        # as a sanity check, make sure we're producing data in the format
        # we SAID we would be producing it, by checking it against our
        # output schema
        validate(memory_table, self.__output_schema)
        return memory_table

    @memtab.setter
    def memtab(self, value: Dict[str, Any]) -> None:
        """This is the reverse of the getter - it populates internal structures from a dictionary"""
        validate(value, self.__output_schema)
        self.project = value["project"]
        # Convert address strings to integers if they're in hex format
        symbols_df = pd.DataFrame(value["symbols"])
        if not symbols_df.empty:
            # Convert hex strings to integers for numeric columns
            hex_columns = ["address", "size", "assigned_size", "start", "end"]

            for col in hex_columns:
                if col in symbols_df.columns and symbols_df[col].dtype == object:  # Check if column exists and contains strings
                    # Vectorized conversion: hex strings, then decimal strings, else leave as is
                    col_data = symbols_df[col].astype(str)
                    # Convert hex strings
                    mask_hex = col_data.str.startswith("0x", na=False)
                    symbols_df.loc[mask_hex, col] = col_data[mask_hex].apply(lambda x: int(x, 16))
                    # Convert decimal strings
                    mask_dec = col_data.str.isdigit()
                    symbols_df.loc[mask_dec & ~mask_hex, col] = pd.to_numeric(col_data[mask_dec & ~mask_hex], errors="coerce")
        self.symbols = symbols_df.set_index("address")
        self.regions = pd.DataFrame(value["regions"]).set_index("name")
        self.sections = pd.DataFrame(value["elf_sections"]).set_index("name")
        self.elf_metadata = value["metadata"]
        self.build_metadata = value.get("build", {})

    @property
    def elf(self) -> Optional[Path]:
        """The ELF file being processed, as a path."""
        return self.__elf

    @elf.setter
    def elf(self, value: Path) -> None:
        if os.path.exists(value):
            if self.__elf != value:
                self.__elf = value
                self.__elf_md5 = hashlib.md5(open(self.elf_str, "rb").read()).hexdigest()
            self.elf_metadata = {
                "filename": self.elf_str,
                "size": os.path.getsize(self.elf_str),
                "md5": self.__elf_md5,
                "timestamp": datetime.datetime.fromtimestamp(os.path.getctime(self.elf_str)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "memtab_version": version("memtab"),
            }

    @property
    def elf_str(self) -> str:
        """The ELF file being processed as a string."""
        return str(self.__elf)

    # region map tabulation
    def __merge_results(self, results: Dict[str, ParserResult]) -> ParserResult:
        """Compares the map file against the ELF file, and ensures that the symbols in the map file match the symbols in the ELF file."""
        nm_results = results["nm"]
        readelf_results = results["readelf"]
        return_results = ParserResult()
        return_results.symbols = nm_results.symbols.copy()
        return_results.sections = readelf_results.sections.copy()
        if "map" in results:  # at the moment, nothing to merge otherwise
            map_results = results["map"]

            def __compare_map_sections_against_readelf_sections(map_sections: List[Section], elf_sections: List[Section]) -> None:
                logging.info("Comparing map file against ELF sections...")
                # First compare the total number of sections
                elf_sections_count = len(elf_sections)
                map_sections_count = len(map_sections)

                if elf_sections_count != map_sections_count:
                    logging.warning(f"Section count mismatch: ELF file has {elf_sections_count} sections, " f"map file has {map_sections_count} sections")
                else:
                    logging.info(f"Section count matches: {elf_sections_count} sections in both ELF and map files")

                for elf_section in elf_sections:
                    elf_name = elf_section.name
                    for map_section in map_sections:
                        if elf_name == map_section.name:
                            elf_size = elf_section.size
                            map_size = map_section.size
                            elf_addr = elf_section.address
                            map_addr = map_section.address
                            if elf_size != map_size:
                                logging.warning(f"Size mismatch for section {elf_name}: ELF size {elf_size} != Map size {map_size}")
                            else:
                                logging.info(f"Section {elf_name} size matches: {elf_size}")
                            if elf_addr != map_addr:
                                logging.warning(f"Address mismatch for section {elf_name}: ELF address 0x{elf_addr:08x} != Map address 0x{map_addr:08x}")
                            else:
                                logging.info(f"Section {elf_name} address matches: 0x{elf_addr:08x}")

                            # if we found a matching map section, we can break out of the inner loop
                            break
                    else:
                        logging.warning(f"No matching map section found for ELF section {elf_section.name}")

            __compare_map_sections_against_readelf_sections(map_results.sections, readelf_results.sections)

            def __compare_map_symbols_against_nm_symbols(map_symbols: List[Symbol], nm_symbols: List[Symbol]) -> List[Symbol]:
                """Compares map symbols against nm symbols."""

                symbols_to_merge: List[Symbol] = []
                map_symbol_names = set(map_symbols)
                nm_symbol_names = set(nm_symbols)

                # Check for symbols in map but not in nm
                map_only_symbols = map_symbol_names - nm_symbol_names
                if map_only_symbols:
                    logging.warning(f"Found {len(map_only_symbols)} symbols in map file not in nm output")
                    for symbol in map_only_symbols:
                        if "bss" in symbol.elf_section and "classifier" in symbol.name:
                            symbols_to_merge.append(symbol)
                        logging.warning(f"Map symbol {symbol.name} not found in nm output")

                # Check for symbols in nm but not in map
                nm_only_symbols = nm_symbol_names - map_symbol_names
                if nm_only_symbols:
                    logging.warning(f"Found {len(nm_only_symbols)} symbols in nm output not in map file")
                    for symbol in nm_only_symbols:
                        logging.warning(f"Nm symbol {symbol.name} not found in map file")
                return symbols_to_merge

            extra_map_symbols = __compare_map_symbols_against_nm_symbols(map_results.symbols, nm_results.symbols)
            return_results.symbols.extend(extra_map_symbols)

        return return_results
