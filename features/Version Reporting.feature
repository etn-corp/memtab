Feature: Reporting Version

Scenario: Version Reporting
    Given I have the memory tabulator package
    When I run the version command
    Then the version should be reported
