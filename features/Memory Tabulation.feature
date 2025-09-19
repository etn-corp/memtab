Feature: Memory Tabulation of an ELF file
  As a developer
  I want to be able to see the memory tabulation of an ELF file
  So that I can make engineering decisions about the footprint of different libraries, methods, etc.
  The output should be in JSON format, to be parsable downstream by other tools.
  It could potentially also generate more immediately human-readable outputs, like images too.
  Finally, it could be in a relational-database format, optimized for more long-term storage, and being co-located with other build metadata.

  Scenario Outline: Memory tabulation of an ELF file
    Given a <toolchain> ELF file
    And <configuration> files describing the memory layout of the target device, the toolchain, and the categories and subcategories of memory
    And <environment> variables
    When I run the memory tabulation command with <arguments> arguments
    Then I should see the memory tabulation of the ELF file broken down into <output> output.
    # ground truth could be the zephyr ROM report, or arm-none-eabi-size text + data,
    # could also check against the hex file, the map, the .bin
    And the <output> should be correlated to a ground truth.

    Examples:
        | toolchain     |  configuration   |  environment   |  arguments   |   output           |
        | x86           |  x86             |                |              | JSON               |
        | cube          |                  |                |  check       | JSON               |
        | cube          |  cube            |                |  check       | JSON               |
        | arm           |  arm             |                |  check       | JSON               |
        | cpp           |  cpp             |                |  check       | JSON               |
        | local_source  |  local_source    |                |  check       | JSON               |
        | local_source  |  local_source    |                |  markdown    | JSON and Markdown  |
        | blinky        |  blinky_include  |                |  check       | JSON               |
        | blinky        |  blinky          | GitHub Action  |  check       | JSON               |
        |               |                  | Memtab Env     |  check       | JSON               |
        # this next line, the "all blank" row, is testing the default values (zephyr.elf, memtab.yml, no env vars)
        # we specify "defaults" in environment because we want to run it in a separate folder,
        # otherwise it would mess up other tests that don't specify each value.
        |               |                  | Defaults       |  check       | JSON               |
        # this next row is a test of the ELF file specified in the YAML config file
        |               |  blinky_with_elf |                |  check       | JSON               |

   Scenario: Supplementing the ELF file with a Map File
    Given an ELF file
    And a map file
    And no additional environment variables
    And configuration files describing the memory layout of the target device, the toolchain, and the categories and subcategories of memory
    When I run the memory tabulation command with map arguments
    Then I should see the memory tabulation of the ELF file broken down into JSON output.
    And the memory tabulation should contain additional information only available in the map file.
