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

Summing up ELF Sections To match binutils ``size`` command
===========================================================

This command will sum up the size of all symbols by ELF section. It will group the symbols by their ELF section and sum up their sizes. The result will be a JSON object with the ELF sections as keys and the total size as values.

.. code-block:: bash

    jq '[
        .symbols[]
        | select(.elf_section != null)
        | {section: .elf_section, size: .size}
        ]
        | group_by(.section)
        | map({(.[0].section): map(.size) | add})
        | add' memtab.json

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
