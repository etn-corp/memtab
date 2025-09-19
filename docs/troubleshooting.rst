###############
Troubleshooting
###############

*********************
Errors Running Memtab
*********************

Unexpected Symbols in Output
-----------------------------
* if you are seeing a `$d` or `$t` in the output symbols, then you likely do not have the gcc-prefix configured correctly. Refer to the :doc:`usage` page, specifically the subsection on configuration, for more detail.

Unexpected Error Messages
-------------------------

KeyError: size
^^^^^^^^^^^^^^

.. code-block:: console

    KeyError: 'size'

This usually occurs if you passed a non-elf file as the elf argument. Make sure you got the right file.

Missing Symbols in Output
-------------------------
If you see symbols in the map file that aren't appearing in the ELF output, please open an Issue on Github.

Incorrect Paths in Output
-------------------------
Some care was taken to attempt to normalize paths.  For example, when applications are built in Windows, and then memtab is run in Linux, or vice versa, the paths as reported by binutils. may not match up.
Furthermore, the ``nm`` utility prepends ``DW_AT_comp_dir`` onto each path, which results in paths that are longer than intended, with the "C:\\" portion appearing twice.  We put in some measures to address this,
specifically by reading in ``DW_AT_comp_dir`` and removing it from the path if it is present.  However, this may not work in all cases, and if you are seeing paths that are not what you expect, please open an issue.

Some anticipated areas that might be problematic:
- Relative Paths - these won't have the anchor folder, so pathlib may not be able to determine the root OS properly.
- Linux paths which have a ``\`` or ``\\`` in them.
- UNC Paths (network mapped paths on Windows)
