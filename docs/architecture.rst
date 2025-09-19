======================
Project Architecture
======================

Overview
--------

The memtab package is designed with modularity in mind, separating different aspects of functionality
into distinct modules. This document describes the overall architecture of the project and the
rationale behind the design decisions.


The general proess the application follows is:


.. mermaid::

    flowchart TD
        A[Run Command Line Tools] --> B[Memtab Constructor]
        A'[Call from Python] --> B
        B --> C[Load Configuration]
        C --> D[Parse Output]
        D --> E[Categorize Symbols]
        E --> F[Visualize Data]
        F --> G[End]

This is the high-level overview of how the application works.  A few parts of that warrant more detail, in particular the "Parse Output", "Categorize Symbols", and "Visualize Data" steps.


Parse Output
----------------

Since there are many possible ways that you can get data for a memory table builder, we have created a ``MemtabParser`` base class that defines the interface for all the parsers.
Each parser takes in a file, implements a ``run`` method for parsing the file, and provides the memtab related data on the ``result`` attribute.

.. mermaid::

    flowchart TD
        A[Build List of Parsers] --> B{More Parsers}
        B -->|Yes| C[Run Parser Command]
        C --> D[Parse Command Output into Sections and Symbols]
        D --> B
        B ---->|No| E[End]



Categorize Symbols
------------------

Symbol categorization is really the heart of memtab.  The categorization logic is separated from the parsing logic to allow for flexibility in how symbols are categorized. The categorization process involves:

1. Loading configuration that defines categories and patterns
2. Analyzing parsed symbols to assign them to categories based on the configured patterns


Visualize Data
----------------

After data has been parsed and categorized, the next step is to visualize it. The visualization module provides functionality to generate visual representations of the memory data, such as graphs or tables. This can be done using various libraries or custom rendering logic.

To make this easier and more extensible in the future without mandating updates to memtab, we have separated visualization out into plugiins.  More on this can be found in the viz documentation.



Project Structure
-----------------

The memtab package is structured as follows:

.. code-block:: text

    src/memtab/
    ├── __init__.py        # Package initialization
    ├── categorizer.py     # Symbol categorization logic
    ├── cli.py             # Command-line interface
    ├── memtab.py          # Main coordinator and integration point
    ├── models.py          # Shared data structures
    ├── viz.py             # Visualization functionality
    └── vizhookspecs.py    # Visualization hook specifications
    └── parsers/           # Raw Input Data parsers
        ├── base.py        # Base class for parsers
        ├── map.py         # Parser for map files
        ├── nm.py          # Parser for nm output
        ├── readelf.py     # Parser for readelf output
        ├── objdump.py     # Parser for objdump output
        ├── size.py        # Parser for size output
    └── schemas/           # JSON schemas for configuration and output
        ├── memtab_config_file_schema.json
        ├── memtab_config_schema.json
        └── memtab_schema.json

Module Responsibilities
-----------------------

models.py
~~~~~~~~~

This module defines the common data structures used across the package. These include:

- ``Symbol``: Represents a symbol (function, variable, etc.) in a binary
- ``Section``: Represents a section in a binary (e.g., .text, .data)
- ``Region``: Represents a memory region in the target system
- ``SubRegion``: Represents a subdivision of a memory region
- ``ParserResult``: Common structure for parser outputs
- ``MemtabConfig``, ``MemtabCPU``, ``MemtabSourceCode``, ``MemtabCategory``: Configuration structures

By centralizing these data structures, we ensure consistency across different components and make it
easier to pass data between modules.

Parser Modules
~~~~~~~~~~~~~~

Each parser module (``nm.py``, ``readelf.py``, ``objdump.py``, ``size.py``,
``map.py``) is responsible for parsing the output of a specific tool and converting it into
the common data structures defined in ``models.py``. Each parser module:

1. Takes the raw output of a command as input
2. Parses the output into structured data
3. Returns a ``ParserResult`` containing sections, symbols, regions, and metadata

.. hint::

    We might expand to a full plug-in style system for parsers, like we did with visualization, in the future.  This could allow for even more data sources than ELF and MAP files.

This modular approach allows for:

- Independent development and testing of parsers
- Easier maintenance when command output formats change
- Consistent handling of data from different sources

categorizer.py
~~~~~~~~~~~~~~

This module is responsible for assigning categories to symbols based on configured patterns and rules.
It analyzes symbol names, file paths, and other attributes to determine which categories a symbol
belongs to. By separating this logic from the parsers:

1. We ensure consistent category assignment regardless of the data source
2. We can delay category assignment until after all input processing is complete
3. We avoid duplicating categorization logic across parsers

memtab.py
~~~~~~~~~

The main class that coordinates the overall process:

1. Handles configuration loading
2. Runs the necessary command-line tools
3. Coordinates parsing through the appropriate parser modules
4. Manages symbol categorization after all parsing is complete
5. Generates the final output


viz.py
~~~~~~~~~

This module contains a markdown report generator, in line with the visualizer plugin system.  This is a similar concept to parsers, but with a more thorough plug-in registry.

Design Rationale
----------------

Separation of Concerns
~~~~~~~~~~~~~~~~~~~~~~

The primary design principle is separation of concerns:

- Parsing logic is isolated in dedicated parser modules
- Data structures are centralized in models.py
- Categorization logic is separated from parsing

This separation makes the code more maintainable and testable, and allows for easier extension
when adding new data sources or categories.

Common Data Structures
~~~~~~~~~~~~~~~~~~~~~~

Using common data structures across all modules ensures that data can flow seamlessly between
components. The ``ParserResult`` class provides a consistent interface for all parsers, making
integration simpler.

Delayed Categorization
~~~~~~~~~~~~~~~~~~~~~~

For the reasons up above in the categorizer section, we delay categorization until after all sources are processed.

Conclusion
----------

The modular architecture of memtab enables flexible processing of various input formats while
maintaining consistency in how data is structured and categorized. This approach facilitates
maintenance and future extensions to support additional data sources or analysis techniques.
