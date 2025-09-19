Feature: Caching data to speed up repeated runs
  As a memtab user
  I want memtab to cache the output of long-running commands
  So that I can speed up repeated runs and debug faster
  Background:
    Given I have a memtab instance

  Scenario: Caching command output
    Given the cache is empty
    When I run the same memtab command twice
    Then the second run should be faster than the first

  Scenario: Clearing the cache
    Given the cache is populated
    When I run the command "memtab --clean"
    Then the cache should be cleared
