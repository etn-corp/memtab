############################
Map Files
############################

In addition to elf files, ``memtab`` accepts an optional map file as input. This is useful for applications that do not have an ELF file, such as those built with the `gcc` toolchain without debug symbols, or for applications that are built with a different toolchain that does not produce ELF files.
This is _not_, however, the default behavior, and you must explicitly pass the map file to the ``--map`` argument. This is for the following reasons:

1. The map file is not a standard output of all toolchains, so it is not always available. (Technically the ELF also isn't mandatory, as it still needs to be converted to hex, bin, srec etc. before loading, but its much closer than a map file is.)
2. The map file format is not as standardized or well documented as the ELF file format, so it may not be as reliable or consistent across different toolchains.
3. The map file does not contain as much information as the ELF file, so it may not be able to provide as much detail about the application. For example - the line numbers into source code of symbols are not available in the map file.
4. Relationships between symbols are not available in the map file, so it is not possible to determine which symbols are related to each other, such as which symbols are referenced by a particular function or which symbols are part of the same data structure.
5. The map file does not demangle any C++ names, which makes it a bit more difficult to track back to original source code, especially in the case of overloaded functions or templates.

That said, there is some information that is available in the map file that is not guaranteed to be available in the ELF file, especially in situations where 3rd party libraries are being used, and where debug information may have been stripped.
For example, with STMicroelectronic's "NanoEdgeAI" tool, the output is an archive (.a) file, which contains a single object (.o) file.  This object is not explicitly stripped, but it does not contain debug information.
This makes it so not all of the symbols are able to be tracked by their names all the way into the .elf file, though they do make it to the .map file.  By using the .map to supplement the .elf, we are able to get a more complete picture of the application.


***********************
Approach
***********************

Using 3rd party library ``Mapfile-parser``
==========================================

We first tried using the `mapfile-parser package available on PyPI <https://pypi.org/project/mapfile-parser/>`_ to read in the map file.  This is a pretty rudimentary package, but it helps avoid some of the boilerplate of actually processing the map file line by line.
After it reads the map file, we can loop through the segments it found and compare those against the sections we have in the .elf file, compare the number of symbols within each, and so on.

However, we quickly found that it did **not** fully read all the data that was captured in the map file.
When we compared the results here against the elf file list, there were certain symbols in the elf file that showed up as not found in the map file, but when you searched for them manually, they were obviously present, meaning this utility did not read as exhaustively as desired.

We briefly considered augmenting the existing solution, but due to relatively low adoption rates (given GitHub star count), and the relative simplicity of the problem at hand (it would take minutes or hours, not days, to get to the same point as this package), we moved on to a different approach.

DIY Solution
==========================================

After the issues we ran into with the `mapfile-parser` package, we decided to write our own parser for the map file.  The mapparser class serves this purpose.
It was written with the express purpose of reading in the map file and structuring the data that can be parsed from it in a similar manner to the way the ELF data was structured.
This is to facilitate an easier comparison between the two data sources.

One library we referenced while working on this solution was the `linkermapviz <https://github.com/PromyLOPh/linkermapviz>`_ library.
Specifically, they had the notion of not processing the output by lines, but instead as a stream.
They could then do regex pattern matching across multiple lines, which is helpful for processing map files.
