Feature: Creating Visualizations
    As a developer
    I want to create visualizations from the memtab output
    So that I can quickly diagnose and describe embedded binaries.

    Scenario: Generating Visuals from Memtab Output
        Given a memtab JSON file
        When I run the memtab visualizer tool with a report specified
        Then I should see a visualization generated from the memtab output
