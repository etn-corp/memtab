Feature: Provide a file describing the output data format
    As a developer
    I want to be able to see the schema of the output data format
    So that I can make engineering decisions about the footprint of different libraries, methods, etc.
    The output should be in JSON format, to be parsable downstream by other tools.

    Scenario: Provide a file describing the output data format
        Given I have the memory tabulator package
        When I run the schema command
        Then I should be provided the schema file
