Usage
=====

Getting Started
----------------

The overall purpose of this tool is two-fold:
1. To generate a memory table from a given set of data
2. To categorize that memory data based on typical "human" methods, such as pattern matching against the directory name or file name of the source code or symbol name from the source code

Future versions of the tool may support other methods of categorization, such as by the region of memory the symbol gets placed in by the linker, or by the type of symbol (e.g. function, variable, etc.).
We may also add support for logical operators on the existing categorization methods, such as AND, OR, NOT, etc.

The tool is designed to be used as a command line tool, but it can also be used as a library in other Python projects.

Philosophy
----------------

The goal is that the tool's purpose is focused. This is in the spirit of the `Unix philosophy <https://en.wikipedia.org/wiki/Unix_philosophy>`_ , specifically items #1 and #2:
      1. Make each program do one thing well. To do a new job, build afresh rather than complicate old programs by adding new "features".
      2. Expect the output of every program to become the input to another, as yet unknown, program. Don't clutter output with extraneous information. Avoid stringently columnar or binary input formats. Don't insist on interactive input.


This program reads in the output of another program (an ELF file), does one thing (categorizes the symbols defined therein) and produces a human and machine readable output file (in JSON format).


The idea there is that any number of downstream tools, like PowerBI, Grafana, a cloud database like anything on AWS, azure, or Snowflake, etc. could all be used to import the data, and then produce visuals, either on a single binary, or show trends over time.


Another key attribute of the philosophy of ``memtab`` is this premise:

   the size of the output can be calculated as the sum of the size of its smallest parts

This means that rather than starting "top down", looking at the file, or the sections of the file, ``memtab`` instead goes "bottom up", summing up sizes at the symbol level.




Installation
------------

To use memtab, first install it using pip:

.. code-block:: console

   (.venv) $ pip install memtab

.. warning::
   After installing the python package, this should be on your PATH environment variable, in both Windows and Linux. Make sure to check the output of the pip install command though,
   sometimes if run as a user, the directory into which it places executables is not on your PATH, and pip will warn you about that.


Command Line Interface
-------------------------
The command line interface (CLI) is the main way to interact with memtab. It is a simple command line tool that can be used to generate memory tables from a given set of data.

The command line function is `memtab`. run `memtab --help` to see the available options.

.. code-block:: console

   (.venv) $ memtab --help

   Usage: memtab [OPTIONS]

   The main command line entry point for calling the memory tabulator. If you want to call memtab from a python app, you should import it directly, NOT via this cli method.

   ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
   │ --elf                                   FILE    The elf file to process. Can also be set via the MEMTAB_ELF environment variable, or defined in the yml config file. [env var: MEMTAB_ELF] [default: zephyr.elf]                                                                                                         │
   │ --config                                PATH    The yml config file(s). Can be provided multiple times. [env var: MEMTAB_YML] [default: memtab.yml]                                                                                                                                                                      │
   │ --json                                  PATH    The JSON file to write out to [default: memtab.json]                                                                                                                                                                                                                     │
   │ --report                                REPORT  Generate report(s) via a plugin. Can be provided multiple times. If you wish to provide a filename, use a : delimiter, like --report markdown:file.md.  If none is provided, it will use a default filename determined by the plugin itself. [default: None]             │
   │ --check                 --no-check              Sanity check the data against size, objdump and readelf [default: no-check]                                                                                                                                                                                              │
   │ --cache                 --no-cache              Use cached data [default: no-cache]                                                                                                                                                                                                                                      │
   │ --clean                 --no-clean              Clean the cache [default: no-clean]                                                                                                                                                                                                                                      │
   │ --map                                   FILE    The map file to process [env var: MEMTAB_MAP] [default: None]                                                                                                                                                                                                            │
   │ --version               --no-version            Show the version of memtab [default: no-version]                                                                                                                                                                                                                         │
   │ --install-completion                            Install completion for the current shell.                                                                                                                                                                                                                                │
   │ --show-completion                               Show completion for the current shell, to copy it or customize the installation.                                                                                                                                                                                         │
   │ --help                                          Show this message and exit.                                                                                                                                                                                                                                              │
   ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Note that the default values for the ``--elf`` and ``--config`` arguments can be set via environment variables, or in the configuration file itself.  Additionally, the ELF file can be specified in the configuration file itself.


Output Data Format
^^^^^^^^^^^^^^^^^^

The output data format for memtab is primarily JSON. The tool will generate a JSON file containing the memory usage information of the code being analyzed. This JSON file can be used for further processing or visualization.

More on the output data format can be found in both the :doc:`postprocessing` and :doc:`output` pages.

Reports
^^^^^^^^^

While more detail on reports can be found on the :doc:`memtab.viz` page, the memtab tool can generate a markdown report of the memory usage of the code. This is useful for generating documentation for the code, and for checking the memory usage of the code.


Reports are generated via the ``--report`` argument, as mentioned above in the help output.  This argument supports an optional filename, which will be used to write the report to.  If no filename is provided, the report will be written to a default filename determined by the plugin itself.

The delimiter between the report name and filename is ``:``.  This means you can run the command two different ways:

.. code-block:: console

   memtab --report markdown:report.md
   memtab --report markdown

The former will write the report to the file ``report.md``, while the latter will write the report to a default filename determined by the plugin itself.  The default filename is typically the ``elf`` filename with the extension replaced, and sometimes more text added to the filename.


Auto-Completion for Reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. termynal:: termynal:report_auto_completion


As alluded to in the above terminal window, this project is using `typer's autocompletion feature <https://typer.tiangolo.com/tutorial/options-autocompletion/>`_ to provide auto-completion for the report names.  This allows some level of self-discoverability for which reports are available on your system.


.. note::

   We considered allowing each report plugin to provide its own argument.  So instead of:

   .. code-block:: console

      # default filename
      memtab --report markdown
      # or, with an explicit filename:
      memtab --report markdown:report.md

   you would do:

   .. code-block:: console

      # default filename
      memtab --markdown
      # or, with an explicit filename:
      memtab --markdown report.md

   However, we avoided this approach for two reasons:
   1. It reduces the effectivity of the ``--report`` "auto-completion" capability described above.
   2. It increases the complexity of the typer command setup in cli.py.  Right now, all of the arguments can be more-or-less "static" parameters to the method.  This approach would require that the parameter list for the command itself by dynamic, and determined by the available plugins.  It is likely do-able, but more complex than what we have today.

Configuration
-----------------
The configuration file is a YAML file that contains the configuration for the memory tabulator. It is used to specify the input data, the output data, and the options for the memory tabulator.
The schema for the configuration file is bundled with the project, and can be found in the `src/memtab/schemas/memtab-config-schema.json` file.
The schema is used to validate the configuration file, and to provide autocompletion for the configuration file. If you are using an IDE like VSCode, consider using this schema to validate the file while you are editing it for faster feedback.

The sections of the configuration:

#. CPU
    #. gcc-prefix
    #. name
    #. memory-regions
        #. RAM
#. Source Code
      #. Categories


Multiple Configuration Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes there may be reasons you want to have multiple configuration files.
For example, you may want to have a different configuration file for each target processor, or for each project.
Another reason is you may want one shared file for definitions specific to a shared platform, and then project specific files that layer detail on top of that.  Memtab supports this.

It is supported two different ways.  First, you can pass in multiple configuration files on the command line.  The files will simply be concatenated together, and the last file will override any duplicate keys in the previous files.
Second, you can use the `include` key in the configuration file.  This key is a list of configuration files to include.  The files will be concatenated together, and the last file will override any duplicate keys in the previous files.

Here is an example of each method:


.. code-block:: bash

   # command line
   memtab --config cpu_1_config.yml --config platform_config.yml

   # include key in the configuration file
   memtab --config full_project_config.yml


.. code-block:: yaml

   # cpu_1_config.yml
   cpu:
     gcc-prefix: arm-none-eabi-
     name: cortex-m4
     memory-regions:
       - name: RAM
         start: 0x20000000
         size: 0x20000

   # cpu_2_config.yml
   cpu:
     gcc-prefix: arm-zephyr-eabi-
     name: cortex-m0
     memory-regions:
       - name: RAM
         start: 0x20000000
         size: 0x10000

   # platform_config.yml
   Source Code:
      root: "/"
      categories:
         - name: Zephyr
            categories:
               - name: Sdk
                  patterns: ["zephyr-sdk", "zsdk"]
               - name: Drivers
                  patterns: ["zephyr/drivers"]
               - name: Lib
                  patterns: ["cpp/"] # important to include the trailing slash to not match on the .cpp extension
               - name: OS
                  patterns: ["sched.c", "mutex.c"]

   # full_project_config.yml
   include:
     - cpu_1_config.yml
     - platform_config.yml

.. WARNING::
   Note that there is very little protection against configurations that override one another.  So to use the above examples you could do this:


   .. code-block:: bash

      memtab --config cpu_1_config.yml --config platform_config.yml --config cpu_2_config.yml

   or alternatively:

   .. code-block:: yaml

      # redundant_project_config.yml
      include:
      - cpu_1_config.yml
      - cpu_2_config.yml  # this line will essentially override the previous line
      - platform_config.yml

   and then:

   .. code-block:: bash

      memtab --config redundant_project_config.yml

   This would not produce any errors (though it may produce warnings in the printed output on the terminal, depending on your logging configuration), but the definitions from ``cpu_2_config.yml`` would override the definitions from ``cpu_1_config.yml``.  So be careful with this feature.



Configuring your System
-------------------------
As you can see, there is an optional `gcc-prefix` element to the configuration. This is because the memory tabulator uses the `objdump` and `readelf` tools to get information about the ELF file.
Now, these tools are part of the `binutils` package, which is typically installed on Linux systems. However, there are also toolchain specific variations to the binutils, and using the toolchain that
corresponds to the gcc/g++ compiler, or at least to the target processor (ARM, vs. x86) will help ensure that the memory tabulator can read the ELF file correctly. So you will need to install the toolchain,
and ensure all of those binutils are on your machine's PATH environment variable.

Note that if this is too burdensome, there is a docker container available. See the :doc:`docker` section for more information.

Output
-----------------
The output of the memory tabulator tool is a JSON file. The schema for this file can be found in `src\memtab\schemas\memtab-schema.json`. This file is used to validate the output of the memory tabulator.
If you are using an IDE like VSCode, consider using this schema to validate the file while you are editing it for faster feedback.

This can be useful if you are working on a downstream consumer of the memtab output - you can use this file to set up your consumer to know the format of the input data.


Workflow
--------

The typical workflow is:

1. The user creates a `Memtab` instance, specifying the ELF file and configuration.
2. The `tabulate()` method is called, which:
   a. Runs various tools (nm, readelf, etc.) to extract data from the ELF file
   b. Parses the output using the appropriate parser modules
   c. Categorizes symbols based on the configuration
   d. Produces a structured DataFrame with the results
   e. If a ``map`` argument is provided, it will also parse the map file using the `MapFileParser` class, and merge the results into the DataFrame.
