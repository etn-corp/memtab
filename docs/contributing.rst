Contributing
============

One goal with this project is that we remain focused on the `behaviors` we want the product to produce.
Nearly all other concerns should be able to be codified in things like the .pre-commit-config.yml file,
the .github/workflows files, the .gitignore file, and the pyproject.toml file.

As such, we are leveraging Behavior Driven Development, and more specifically, the gherkin syntax for
specifying behavior in an executable fashion using Given/When/Then statements. These statements are captured
in plaintext, in feature files are in the `features` directory, and the tests that implement those features are in the `tests` directory.
You can find more detail on this in the `testing` section.


Guidelines
----------
#. Install Precommit and remain compliant with that ruleset
#. Install and use the `uv` tool to run the various commands
#. Ensure we maintain code coverage
    #. This is enforced by the coverage requirement embedded in the pytest github workflow.
    #. If you are writing code that is not covered by the existing tests, either
        #. add a new test
        #. consider if the code you are writing is necessary, as the existing tests cover existing requirements.
#. Ensure your code is well documented
    #. this is enforced can be done via the interrogate tool, which is run as part of the precommit checks
#. If you are updating the config file format of the tool, ensure you do the following:
    #. Update the config section of `docs/usage.rst` file to reflect those changes
    #. Update the `src/memtab/schemas/memtab-config-schema.json`
#. If you are updating the output format of the tool, ensure you do the following:
    #. Update the output data processing section of `docs/usage.rst` file to reflect those changes
    #. Update the `src/memtab/schemas/memtab-schema.json`
#. Update the project version number.
    #. This is done in the `pyproject.toml` file, and should follow semantic versioning principles.
#. Open pull requests against the `main` branch
    #. Ensure your PR passes all checks
    #. Ensure your PR is reviewed and approved by at least one other person
    #. Ensure your PR is merged using the "Squash and Merge" option, to ensure a clean commit history

For more details on what precommit checks are run, see the `.pre-commit-config.yaml` file, and the :doc:`precommit` section.

Developer Signoff
-----------------

By contributing code to this project, you agree to the following:

#. You have the right to submit the code you are contributing, and it does not violate any third party rights.
#. You agree to license your contributions under the `MIT License <https://opensource.org/license/mit/>`_.
#. You agree to the Developer Certificate of Origin (DCO) as described in the `DCO 1.1 <https://developercertificate.org/>`_.

If you do not agree to these terms, please do not contribute code to this project.
The DCO is enforced via a pre-commit hook.
