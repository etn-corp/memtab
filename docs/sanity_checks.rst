Sanity Checks
================

If you run with the `--check` argument, memtab will perform a few "sanity checks" against some other tools that produce similar measures of memory resource utilization.


Comparing Against `size` Output
-------------------------------


The `size` tool, from GNU's binutils, provides the highest level assessment of the memory usage of an ELF file.  It provides a breakdown of the memory usage by section, and also provides a total for the entire ELF file.
The output of `size` is in the following format:

    text    data     bss     dec     hex filename
    1234    5678    9101   12345   0x3039 my.elf

Memtab will run `size`, capture the output, and then compare the numbers from size against the numbers from `readelf` described in the next section.


Comparing Against `readelf` Output
----------------------------------


Readelf can output details at a few levels.  One level is the "section", which should be on the dozens-of-lines territory.  You can also output at the symbol level, which will be hundreds or thousands of lines, similar to `nm`.

The output of `readelf` is in the following format:

    Section Headers:
    [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
    [ 0]                   NULL            00000000 000000 000000 00      0   0  0
    [ 1] .interp           PROGBITS        00000000 000040 00001c 00   A  0   0  1
    [ 2] .note.gnu.build-id NOTE            00000000 00005c 000024 00   A  0   0 16
    [ 3] .gnu.hash         GNU_HASH        00000000 000080 000030 04   A 10   0 16
    [ ... ]

And then symbols are listed in the following format:
    Symbol table '.symtab' contains 1234 entries:
       Num:    Value          Size Type    Bind   Vis      Ndx Name
         0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND
         1: 0000000000000000     0 SECTION LOCAL  DEFAULT    1
         2: 0000000000000000     0 SECTION LOCAL  DEFAULT    2
         ...
         1233: 0000000000401000     4 OBJECT  GLOBAL DEFAULT   10 _start

Memtab will run `readelf`, capture the output, and the compare the numbers from readelf against the numbers from `size` described in the previous section.
It also uses readelf though to get the total sizes for each region, as well as the addresses covered, so it can allocate symbols to those regions.


Comparing Against `objdump` Output
----------------------------------


Objdump is similar to `readelf`, and as such is currently used the least.  We just run `objdump`, capture the output to local memory, and compare against the other tools like `size` just to make sure the numbers make sense together.
It is currently not used to inform the overall output of memtab at all.




Comparing Against the `ld` `--print-memory-usage` Output
--------------------------------------------------------
The `ld` linker has a `--print-memory-usage` option that prints out the memory usage of the different regions defined in the linker script.  More documentation on that can be found `here <https://sourceware.org/binutils/docs-2.31/ld/Options.html>`_.

Unfortunately, this requires the link operation to actually occur - as in, the inputs are the linker script and all of the .o files that are being linked together to produce the .elf.
At the time of this writing, I could not determine a way to produce this output given just the elf, or even the elf + a linker script.

Therefore, to perform this sanity check, we will have to copy off the output of the `--print-memory-usage` to a separate file, and then compare the memtab results against the data in that file.  Its not perfect, but its better than nothing.

Note - to get this in zephyr, you need to define `OUTPUT_PRINT_MEMORY_USAGE` in your KConfig settings.
