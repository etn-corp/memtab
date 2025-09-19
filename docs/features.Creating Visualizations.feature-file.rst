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

:gherkin-feature-keyword:`Feature:` :gherkin-feature-content:`Creating Visualizations`
======================================================================================

    :gherkin-feature-description:`As a developer`
    :gherkin-feature-description:`I want to create visualizations from the memtab output`
    :gherkin-feature-description:`So that I can quickly diagnose and describe embedded binaries.`

:gherkin-scenario-keyword:`Scenario:` :gherkin-scenario-content:`Generating Visuals from Memtab Output`
-------------------------------------------------------------------------------------------------------

| :gherkin-step-keyword:`Given` a memtab JSON file
| :gherkin-step-keyword:`When` I run the memtab visualizer tool with a report specified
| :gherkin-step-keyword:`Then` I should see a visualization generated from the memtab output

