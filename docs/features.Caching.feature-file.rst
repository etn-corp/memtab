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

:gherkin-feature-keyword:`Feature:` :gherkin-feature-content:`Caching data to speed up repeated runs`
=====================================================================================================

    :gherkin-feature-description:`As a memtab user`
    :gherkin-feature-description:`I want memtab to cache the output of long-running commands`
    :gherkin-feature-description:`So that I can speed up repeated runs and debug faster`

:gherkin-background-keyword:`Background:`
-----------------------------------------

| :gherkin-step-keyword:`Given` I have a memtab instance

:gherkin-scenario-keyword:`Scenario:` :gherkin-scenario-content:`Caching command output`
----------------------------------------------------------------------------------------

| :gherkin-step-keyword:`Given` the cache is empty
| :gherkin-step-keyword:`When` I run the same memtab command twice
| :gherkin-step-keyword:`Then` the second run should be faster than the first

:gherkin-scenario-keyword:`Scenario:` :gherkin-scenario-content:`Clearing the cache`
------------------------------------------------------------------------------------

| :gherkin-step-keyword:`Given` the cache is populated
| :gherkin-step-keyword:`When` I run the command \"memtab --clean\"
| :gherkin-step-keyword:`Then` the cache should be cleared

