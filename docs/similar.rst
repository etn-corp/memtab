############################
Similar Packages
############################

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
