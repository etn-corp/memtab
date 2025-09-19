# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""This module contains the visualization functions for the memtab package.
It includes functions for generating markdown files based on the analysis results.
The generated visualizations help users understand the memory usage and organization of their code.
The module also includes functions for generating memory maps, which provide a visual representation of the memory layout of the code.
"""

import logging
import os

from mdutils.mdutils import MdUtils

from memtab import hookimpl as impl
from memtab.memtab import Memtab


class MemtabMarkdownReportSpec:
    report_name = "markdown"
    symbol_count_cutoff: int = 10
    sort_by_size: bool = True
    reduce_column_count: bool = True

    @impl
    def generate_report(self, memtab: Memtab, filename: str) -> None:
        """This generates a markdown summary file of the memory table report.
        This markdown can be used as a GITHUB_STEP_SUMMARY, for example.
        A reference for why this utility exists can be found here: https://github.com/joonvena/Robot-Reporter
        Documentation on the GITHUB_STEP_SUMMARY use can be found here: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#adding-a-job-summary

        Args:
            response (Memtab): the memtab tabulator containing the data to be summarized.
            md (str): the markdown filename to write to.
            symbol_count_cutoff (int, optional): the point at which to cutoff the table of symbols. Defaults to 10.
            sort_by_size (bool, optional): sort the symbols by size, largest to smallest. Defaults to True.
            reduce_column_count (bool, optional): For brevity, only show key columns. Defaults to True.
        """
        if not filename:
            # Try to get ELF filename from metadata, fallback to generic name
            elf_filename = getattr(memtab, "elf_metadata", {}).get("filename", "")
            if elf_filename:
                filename = str(elf_filename).replace(".elf", ".md")
            else:
                filename = "memtab_report.md"

        # Ensure the directory exists
        file_dir = os.path.dirname(filename)
        if file_dir:
            if not os.path.exists(file_dir):
                logging.info(f"Directory {file_dir} does not exist. Using just the filename.")
                filename = os.path.basename(filename)
        mdFile = MdUtils(file_name=filename, title="Memory Usage Report Summary :bar_chart:")
        symbols = memtab.symbols
        flash = symbols[symbols["region"] == "Flash"]
        ram = symbols[symbols["region"] == "RAM"]
        if self.sort_by_size:
            flash = flash.sort_values(by="size", ascending=False)
            ram = ram.sort_values(by="size", ascending=False)

        flash = flash.head(self.symbol_count_cutoff)
        ram = ram.head(self.symbol_count_cutoff)
        if self.reduce_column_count:
            flash = flash[["symbol", "size", "categories", "file"]]
            ram = ram[["symbol", "size", "categories", "file"]]

        flash_table = flash.to_markdown()
        ram_table = ram.to_markdown()
        mdFile.new_line(f"## Top {self.symbol_count_cutoff} Flash Symbols :arrow_up:")
        mdFile.new_paragraph(flash_table)
        mdFile.new_line(f"## Top {self.symbol_count_cutoff} RAM Symbols :arrow_up:")
        mdFile.new_paragraph(ram_table)

        mdFile.create_md_file()
        logging.info(f"Generated Markdown report: {filename}")
