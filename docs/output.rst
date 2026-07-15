############################
Output Data Format
############################

The output data format for memtab is primarily JSON. The tool will generate a JSON file containing the memory usage information of the code being analyzed.

This JSON file can be used for further processing or visualization.

More on processing the output data format can be found on the :doc:`postprocessing` page.


***********************
Output Schema
***********************

.. jsonschema:: _static/schemas/memtab_schema.json
    :lift_definitions: True
    :auto_reference: True


*************************
Size vs. Assigned Size
*************************

You will notice in the output that there are two different size metrics reported: ``size`` and ``assigned_size``.

- **size** refers to the total memory usage of the object, including any memory "reused" or "shared" with another symbol.
- **assigned_size** is the memory unique to the object itself.

This distinction is important for understanding the true memory footprint of your data structures and can help identify potential optimizations.

There are three distinct scenarios when comparing ``size`` to ``assigned_size``:

1. ``size == assigned_size``

   1. In this scenario, the object does not share/reuse any code, and it is immediately adjacent to the next symbol in memory.

    .. thumbnail:: _static/output_size_and_assigned_size/eq.png

        size == assigned_size

2. ``size < assigned_size``

   1. In this scenario, there is some unused memory between this symbol and the next in memory, and thus that padding is allocated to this symbol.
   See the Wikipedia page on `Data Structure Alignment <https://en.wikipedia.org/wiki/Data_structure_alignment>`_ for more information.

    .. thumbnail:: _static/output_size_and_assigned_size/lt.png

        size < assigned_size

3. ``size > assigned_size``

   1. In this scenario, the object shares memory with another object, leading to a larger reported size.

    .. thumbnail:: _static/output_size_and_assigned_size/gt.png

        size > assigned_size


With these definitions, the design intent is that the sum of ``assigned_size`` should add up to the available size of flash memory.

.. note::

   ``assigned_size`` reflects bytes occupied at **runtime** (VMA space).  For targets where
   initialized data sections (e.g. ``.data``, ``.ramfunc``) are stored in Flash but copied to
   RAM at startup, a symbol's ``assigned_size`` describes its RAM footprint.  The Flash storage
   footprint of those bytes is identical in size, but accounted for at the *section* level via
   the ``lma`` field — see `lma-vma`_ below.


.. _lma-vma:

*****************************
LMA vs. VMA in ELF Sections
*****************************

Every entry in ``elf_sections`` carries two address fields:

- **``address``** — the *Virtual Memory Address* (VMA): where the section is accessed at runtime.
- **``lma``** — the *Load Memory Address*: where the section's bytes are physically stored.  A
  value of ``0`` means the LMA was not parsed or is the same as ``address``.

For most sections (e.g. ``.text``, ``.rodata`` in a typical Flash-based MCU build), ``lma == address``.
The important exception is initialized data:

.. code-block:: text

    .data    0x20000200    0x34    load address 0x0800200c
    ↑ VMA (RAM, runtime)            ↑ LMA (Flash, storage)

Here the ``.data`` init image occupies Flash at ``0x0800200c`` and is copied to RAM at
``0x20000200`` by the startup (``crt0``) code before ``main()`` runs.

Memtab uses the ``lma`` field when calculating region spare values: sections whose LMA (not
only VMA) falls within a Flash region are counted toward that region's usage.  This ensures
the Flash spare is not overstated for targets that copy initialized data from Flash to RAM
at boot — a pattern used by every ROM-based MCU build.

Sections typed ``NOBITS`` (e.g. ``.bss``, ``.noinit``) are **excluded** from the LMA check even
when the linker assigns them a load address, because they contain no bytes in the binary.


********************************
ARM Unwind Attribution
********************************

When ``CPU.exclude_arm_sections`` is set to ``false``, memtab attributes ARM unwind bytes to
symbols using ``.ARM.exidx`` ownership information:

- ``exidx_size``: bytes from ``.ARM.exidx`` attributed to a symbol
- ``extab_size``: bytes from ``.ARM.extab`` attributed to a symbol

Each ``.ARM.exidx`` entry contributes 8 bytes to the owning function. Entries that reference
``.ARM.extab`` contribute additional bytes based on the decoded table entry ranges.

These fields are additive attribution data and are reported alongside ``size`` and
``assigned_size`` for symbol-level analysis of exception handling overhead.


*****************************
Flash Usage with ``jq``
*****************************

.. note::

   The ``jq`` snippet below uses the ``lma`` field introduced in schema 1.3.0.  On older output
   files (schema 1.2.0) ``lma`` is absent; use ``select(.address < 0x20000000)`` as a simpler
   approximation.

To compute true Flash consumption on an ARM Cortex-M target (Flash below ``0x20000000``, RAM at
or above), include both VMA sections and non-NOBITS sections whose LMA is in Flash:

.. code-block:: bash

    jq '
      [.elf_sections[] |
        select(
          (.address < 0x20000000) or
          ((.lma // 0) != 0 and (.lma // 0) != .address and (.lma // 0) < 0x20000000
           and .type != "NOBITS")
        )
      ] | map(.size) | add' memtab.json
