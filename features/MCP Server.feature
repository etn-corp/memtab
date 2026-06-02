Feature: MCP Server
  As a developer
  I want to ask copilot about the memory usage of my elf file
  So that I get a sense of how close we are to certain physical limits

  Scenario: MCP Server
    Given an elf file
    When I ask copilot about the memory usage of that elf file
    Then I should get a response with the memory usage of the elf file in list format
