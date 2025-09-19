.. role:: gherkin-step-keyword
.. role:: gherkin-step-content
.. role:: gherkin-feature-description
.. role:: gherkin-scenario-description
.. role:: gherkin-feature-keyword
.. role:: gherkin-feature-content
.. role:: gherkin-background-keyword
.. role:: gherkin-background-content
.. role:: gherkin-scenario-keyword
.. role:: gherkin-scenario-content
.. role:: gherkin-scenario-outline-keyword
.. role:: gherkin-scenario-outline-content
.. role:: gherkin-examples-keyword
.. role:: gherkin-examples-content
.. role:: gherkin-tag-keyword
.. role:: gherkin-tag-content

:gherkin-feature-keyword:`Feature:` :gherkin-feature-content:`Memory Tabulation of an ELF file`
===============================================================================================

    :gherkin-feature-description:`As a developer`
    :gherkin-feature-description:`I want to be able to see the memory tabulation of an ELF file`
    :gherkin-feature-description:`So that I can make engineering decisions about the footprint of different libraries, methods, etc.`

    :gherkin-feature-description:`The output should be in JSON format, to be parsable downstream by other tools.`

    :gherkin-feature-description:`It could potentially also generate more immediately human-readable outputs, like images too.`

    :gherkin-feature-description:`Finally, it could be in a relational-database format, optimized for more long-term storage, and being co-located with other build metadata.`

:gherkin-scenario-outline-keyword:`Scenario Outline:` :gherkin-scenario-outline-content:`Memory tabulation of an ELF file`
--------------------------------------------------------------------------------------------------------------------------

| :gherkin-step-keyword:`Given` a **\<toolchain\>** ELF file
| :gherkin-step-keyword:`And` **\<configuration\>** files describing the memory layout of the target device, the toolchain, and the categories and subcategories of memory
| :gherkin-step-keyword:`And` **\<environment\>** variables
| :gherkin-step-keyword:`When` I run the memory tabulation command with **\<arguments\>** arguments
| :gherkin-step-keyword:`Then` I should see the memory tabulation of the ELF file broken down into **\<output\>** output.
| :gherkin-step-keyword:`And` the **\<output\>** should be correlated to a ground truth.

:gherkin-examples-keyword:`Examples:`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table::
    :header: "toolchain", "configuration", "environment", "arguments", "output"
    :quote: “

    “x86“, “x86“, ““, ““, “JSON“
    “cube“, ““, ““, “check“, “JSON“
    “cube“, “cube“, ““, “check“, “JSON“
    “arm“, “arm“, ““, “check“, “JSON“
    “cpp“, “cpp“, ““, “check“, “JSON“
    “local_source“, “local_source“, ““, “check“, “JSON“
    “local_source“, “local_source“, ““, “markdown“, “JSON and Markdown“
    “blinky“, “blinky_include“, ““, “check“, “JSON“
    “blinky“, “blinky“, “GitHub Action“, “check“, “JSON“
    ““, ““, “Memtab Env“, “check“, “JSON“
    ““, ““, “Defaults“, “check“, “JSON“
    ““, “blinky_with_elf“, ““, “check“, “JSON“

:gherkin-scenario-keyword:`Scenario:` :gherkin-scenario-content:`Supplementing the ELF file with a Map File`
------------------------------------------------------------------------------------------------------------

| :gherkin-step-keyword:`Given` an ELF file
| :gherkin-step-keyword:`And` a map file
| :gherkin-step-keyword:`And` no additional environment variables
| :gherkin-step-keyword:`And` configuration files describing the memory layout of the target device, the toolchain, and the categories and subcategories of memory
| :gherkin-step-keyword:`When` I run the memory tabulation command with map arguments
| :gherkin-step-keyword:`Then` I should see the memory tabulation of the ELF file broken down into JSON output.
| :gherkin-step-keyword:`And` the memory tabulation should contain additional information only available in the map file.

