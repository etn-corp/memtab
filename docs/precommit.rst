Pre-Commit Checks
=================


The pre-commit checks are used for the "quick and easy" enforcement of basic code quality standards.
If you run `pre-commit install`, then these checks are run on every commit, and if they fail, the commit will be rejected.
The checks are run using the `pre-commit` tool, which is a python package that can be installed via pip.


This document serves to describe a few of the checks. It is not to be considered exhaustive - checks may be added or removed over time, and the best way to see what checks are currently being run is to look at the `.pre-commit-config.yaml` file.
The purpose of this page is just to document some specific considerations that are related to these checks.


Static Type Checking via MyPy
-----------------------------

I am using this repository to experiment a bit with adding mypy type checking. Python, in general, is a weakly typed language. Objects can be re-cast, accesses/calls can be made on just about anything and you'll just get an AttributeError if it doesn't exist.
This can be a positive in many ways - it certainly can make development fast, and keeps code concise. However, if you are trying to familiarize yourself with a codebase, untyped variables can be a bit confusing. Mypy attempts to address this by enforcing strong type hints.
Type hints in python are only used at edit time, they are not used at runtime. you can think of them essentially as "disappearing" at runtime.

That said - I am not sure yet how I feel about the value-add of the level of detail mypy requires. I am not sure if it has increased or decreased code readability, maintainabilty, testability… but we're trying it for now.

Mypy configuration resides in the pyproject.toml.

Documentation Checking via Interrogate
--------------------------------------

Interrogate is used to ensure that public methods and classes have docstrings embedded within them. This is a good practice, and helps to ensure that the auto-generated documentation gets non-trivial contents. Interrogate is configured in the pyproject.toml.


Code Complexity Checking via Radon/Xenon
----------------------------------------

We are using xenon to enforce a code complexiity measure. We require everything to be above a "C" grade. No custom configuration is needed - that grade level is set in the precommit yaml file.

Code Formatting via Ruff
------------------------

There are many python formatters available. I am of the opinion that __which__ one you choose is less important than __using__ one. I have chosen to use ruff, as it is fast and has a lot of features. It is also the default formatter for pre-commit, so it is easy to use in that regard.

Gherkin Formatting via Gherkin Lint
-----------------------------------

We figured we might as well put some static analysis enforcement on the feature files as well, since those are perhaps the most often read by a broad audience. Again - picking A standard is more important than which one you pick.
