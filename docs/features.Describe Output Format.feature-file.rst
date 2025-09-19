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

:gherkin-feature-keyword:`Feature:` :gherkin-feature-content:`Provide a file describing the output data format`
===============================================================================================================

    :gherkin-feature-description:`As a developer`
    :gherkin-feature-description:`I want to be able to see the schema of the output data format`
    :gherkin-feature-description:`So that I can make engineering decisions about the footprint of different libraries, methods, etc.`

    :gherkin-feature-description:`The output should be in JSON format, to be parsable downstream by other tools.`

:gherkin-scenario-keyword:`Scenario:` :gherkin-scenario-content:`Provide a file describing the output data format`
------------------------------------------------------------------------------------------------------------------

| :gherkin-step-keyword:`Given` I have the memory tabulator package
| :gherkin-step-keyword:`When` I run the schema command
| :gherkin-step-keyword:`Then` I should be provided the schema file

