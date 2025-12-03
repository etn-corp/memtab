############################
Similar Packages
############################

.. note::
  References to pyelftools, linkerscope, and membrowse are for comparison only. These are independent projects, not affiliated with memtab.
  Any similarities or differences noted reflect my personal opinion and are provided “as is,” without any warranty or representation.
  Reasonable minds may differ. Do not rely on my statements for any action or inaction; any reliance is at your own risk.
  Review and comply with all applicable third-party license terms.


***********************
PyElfTools Library
***********************

The `pyelftools <https://github.com/eliben/pyelftools>`_ library is a pure Python implementation for parsing ELF files. It can be used to extract information from ELF files, including symbol tables and section headers.
One difference is that pyelftools is a library, whereas memtab is a command line tool that produces a specific output format.
Another difference is that pyelftools does not handle ARM binaries, so you will get a lot of not helpful `$d` and `$t` symbols.

***********************
LinkerScope Library
***********************

The `linkerscope <https://github.com/raulgotor/linkerscope>`_ tool is a similar tool that also generates memory usage reports from build outputs.
One difference is this expects a map file as input, rather than an ELF file. This means that it is not able to categorize at the symbol level, but rather at the section level.

***********************
Membrowse
***********************

The `membrowse python package <https://github.com/membrowse/membrowse-action>`_ shares several similarities with memtab, and a few key differences.

Similarities:
  - Both tools analyze ELF files to provide memory usage reports.
  - Both tools provide a GitHub action to expedite integration into CI workflows.
  - Both tools rely on reading the DWARF data out of the ELF file to provide more context about the symbols.

Differences:
  - membrowse requires linker scripts at runtime, not just the elf
  - membrowse is built on pyelftools, whereas memtab is built around the binutils 'nm' command.
  - membrowse provides its own cloud service for storing historical data, whereas memtab is designed to be self-hosted.
    - as part of this, membrowse implements an "onboarding" process to fill out historical data by analyzing previous commits.
  - memtab focuses more on the categorization of symbols

Further investigation into this is warranted - I am curious how the membrowse utility addressed the shortcomings we found with pyelftools.
