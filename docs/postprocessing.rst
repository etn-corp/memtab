############################
Post Processing Data
############################

Here are some examples of ways you could post process the JSON file.

***********************
Visualizing Outputs
***********************


Memtab is focused on parsing the elf file according to a config.  Its output is JSON, and an optional markdown file, primarily intended for GitHub Action step summaries.
By design, it is NOT focused on displaying the output in a friendly manner.  JSON is human readable for debug purposes, but primary is to be machine readable.

You can use other tools like ``jq`` (see below) PowerBI, Grafana, etc. to visualize.  More information on the output file format can be found in :doc:`output` as well.


That said, memtab has also been supplemented with a "plugin" based system using `pluggy <https://pluggy.readthedocs.io/en/stable/>`_ to allow extension so that new reports can be created simply by passing something additional to the command line.

Using this plugin model, you can create your own visualizers.  The plugin system is designed to be simple and easy to use.
You can create a new plugin by creating a new class that inherits from the `BaseVisualizer` class and implementing the `visualize` method.
The `visualize` method should take the output of memtab as input and generate the desired visualization.  You can then register your plugin with the `pluggy` system using the `@hookimpl` decorator.



************
Using ``jq``
************

``jq`` is a command line JSON processor. It can be used to filter and transform JSON data. Here are some examples of how to use ``jq`` to post process the JSON file.

Note that most if not all of the examples in here were generated using GitHub Copilot, showing it the JSON file, and asking it create a command for the specific desired output.  After wrapping your head around these examples, if they don't need your specific need, you should try to do the same!

Understanding Different Size Calculations
==========================================

Memtab provides multiple ways to calculate memory usage, each serving different purposes:

**Symbols vs. ELF Sections vs. Regions**

- **Symbols** (``size`` field): Represent named functions, variables, and objects. These are the entities the compiler/linker tracks. Summing symbol sizes gives you the memory consumed by identifiable code and data.

- **Symbols** (``assigned_size`` field): The symbol's size plus any padding/gaps until the next symbol. This accounts for alignment and fragmentation between symbols within a section.

- **ELF Sections** (``size`` field): The total size of each section in the ELF file as reported by ``readelf``. Sections contain both symbols and additional data like exception tables, initialization arrays, padding, and metadata.

- **Regions**: High-level memory areas (e.g., Flash, RAM) defined in your config. Memtab calculates region usage by summing the ELF sections that fall within each region's address range.

**Why totals differ:**

When you sum up symbol sizes, you'll typically get a **lower number** than the total ELF section sizes because sections contain more than just symbols:

- **Exception handling tables** (``.ARM.extab``, ``.ARM.exidx``) - compiler-generated unwinding information with no individual symbols
- **Initialization arrays** (``init_array``, ``ctors``) - lists of function pointers without individual symbol names
- **Padding and alignment** - gaps between symbols for proper memory alignment
- **Section metadata** - attributes and bookkeeping information

**Which calculation should you use?**

- **Total memory usage**: Sum ELF section sizes (``jq '[.elf_sections[] | select(.address < 0x20000000)] | map(.size) | add'``)
- **Analyzing what code/data contributes**: Sum symbol sizes or use categories
- **Comparing to binutils ``size`` command**: See the section below
- **Fragmentation analysis**: Compare symbol ``assigned_size`` to ``size`` to see gaps

Calculating Size
=========================

This will sum up all sizes:

.. code-block:: bash

    jq '[.symbols[] | .size] | add' memtab.json

This will sum up all sizes for RAM regions:

.. code-block:: bash

    jq '[.symbols[] | select(.region == "RAM") | .size] | add' memtab.json

Summarizing Size By Top Level Category
======================================

This command will summarize the size of all symbols by top level category. It will group the symbols by their top level category and sum up their sizes. The result will be a JSON object with the top level categories as keys and the total size as values.

.. code-block:: bash

    jq '[
        .symbols[]
        | select(.categories != null and .categories["0"] != null)
        | {category: .categories["0"], size: .size}
        ]
        | group_by(.category)
        | map({(.[0].category): map(.size) | add})
        | add' memtab.json

Total Number of Symbols Per Top Level Category
================================================

This one can be useful when you are in the process of categorizing your code, as a quick measure of how many "unknown" symbols you have left.

.. code-block:: bash

    jq '
        .symbols
        | group_by(.categories["0"])
        | map({(.[0].categories["0"]): length})
        | add
        ' memtab.json


Total Number of Symbols Per Top Level Category as Percentage
============================================================

This is similar to the above, but shows it as a prercentage of the overall number of symbols.

.. code-block:: bash

    jq '
        .symbols as $symbols | $symbols |
        group_by(.categories["0"]) |
        map({(.[0].categories["0"]): ((length / ($symbols | length) * 100 * 100 | floor) / 100 | tostring + "%")}) |
        add
        ' memtab.json


Summarizing by ELF section
=================================

.. code-block:: bash

    jq '[
        .symbols[]
        | select(.elf_section != null)
        | {section: .elf_section, size: .size}
        ]
        | group_by(.section)
        | map({(.[0].section): map(.size) | add})
        | add' memtab.json

Correlating with Binutils Tools
=================================

Memtab's output can be correlated with standard binutils tools like ``size`` and ``readelf``.

Matching ``readelf -SW`` Section Sizes
---------------------------------------

To get the total size of ELF sections (matching what ``readelf -SW`` reports), use the ``.elf_sections`` array:

.. code-block:: bash

    # Total size of all ELF sections
    jq '[.elf_sections[] | .size] | add' memtab.json

    # Size of specific sections
    jq '.elf_sections[] | select(.name == "text" or .name == "rodata") | {name, size}' memtab.json

    # Total Flash usage (sections with addresses < 0x20000000, for example)
    jq '[.elf_sections[] | select(.address < 0x20000000)] | map(.size) | add' memtab.json

Each ELF section also includes a ``calculated_symbol_size`` field showing how much of that section is accounted for by symbols:

.. code-block:: bash

    # Compare section sizes to symbol coverage
    jq '.elf_sections[] | {name, size, calculated_symbol_size, gap: (.size - .calculated_symbol_size)}' memtab.json

Sections with zero ``calculated_symbol_size`` (like ``.ARM.extab``, ``.ARM.exidx``) contain compiler-generated data without individual symbol names.

Approximating ``size`` Command Output
--------------------------------------

The binutils ``size`` command reports text, data, and bss segment sizes. You can approximate this from memtab output:

.. code-block:: bash

    # Sum symbol sizes by memory type
    jq '[.symbols[] | select(.memory_type != null) | {type: .memory_type, size: .size}]
        | group_by(.type)
        | map({(.[0].type): map(.size) | add})
        | add' memtab.json

Note that this sums **symbol** sizes, not section sizes. For a closer match to ``size`` output, you may need to sum specific ELF sections based on your linker script.

Categorizing ELF Sections into `WA` Flagged regions
======================================================


This is similar to the above, but it groups all of the sections from readelf that would be flagged ``WA`` together.

.. code-block:: bash

    jq '[
            .symbols[]
            | select(.elf_section != null)
            | {section: (.elf_section | if . | IN("sw_isr_tables", "ctors", "data", "device_states", "k_mutex_area", "bss", "noinit", "eth_stm32") then "WA" else . end), size: .size | tonumber}
        ]
        | group_by(.section)
        | map({(.[0].section): (map(.size) | add)})
        | add' memtab.json

Finding the Heavy Hitters
=================================

This command will find the top 10 largest symbols in the JSON file. It will sort the symbols by size and return the top 10 largest symbols.
.. code-block:: bash

    jq '[
        .symbols[]
        | {name: .symbol, size: .size}
        ]
        | sort_by(.size) | reverse
        | .[0:10]' memtab.json

you could combine it with some of the earlier techniques if you wanted to restrict to RAM or Code, for example.


Reporting size vs. Assigned Size
========================================

The size of an element is its actual size used by the application.  The memtab definition of "assigned size" is the size plus whatever space is available up until the next address.


To sum up assigned sizes for RAM regions:

.. code-block:: bash

    jq '[.symbols[] | select(.region == "RAM") | .assigned_size] | add' memtab.json

To report the summed up sizes along side the summed up assigned sizes, we can run the following variation of an earlier command:


.. code-block:: bash

    jq '[
        .symbols[]
        | select(.elf_section != null)
        | {section: .elf_section, size: .size, assigned_size: .assigned_size}
        ]
        | group_by(.section)
        | map({
            (.[0].section): {
            total_size: (map(.size) | add),
            total_assigned_size: (map(.assigned_size) | add)
            }
        })
        | add' memtab.json


Getting Uncategorized Symbols
=============================

This command will find all symbols that do not have any categories assigned to them. It will return a list of those symbols along with their sizes.

.. code-block:: bash

    jq '.symbols[] | select(.categories["0"] == "unknown") | {symbol, file}' memtab.json


If you just want a quick measure of how many symbols are uncategorized, you can pipe to the ``length`` operator.

.. code-block:: bash

    jq '[.symbols[] | select(.categories["0"] == "unknown")] | length' memtab.json
