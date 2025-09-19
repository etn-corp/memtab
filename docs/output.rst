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
