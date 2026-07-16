Pre-Commit Checks
=================


The pre-commit checks are used for the "quick and easy" enforcement of basic code quality standards.
If you run `prek install`, then these checks are run on every commit, and if they fail, the commit will be rejected.
The checks are run using the `prek` tool, a Rust-native drop-in alternative to pre-commit. It can be installed via ``uv tool install prek``.


This document serves to describe a few of the checks. It is not to be considered exhaustive - checks may be added or removed over time, and the best way to see what checks are currently being run is to look at the `.pre-commit-config.yaml` file.
The purpose of this page is just to document some specific considerations that are related to these checks.


Static Type Checking via ty
-----------------------------

We use `ty <https://docs.astral.sh/ty/>`_ (from Astral, the same team behind ruff and uv) for static type checking.
Python is a dynamically typed language - type hints are only used at edit time and "disappear" at runtime.
ty checks those hints statically, catching bugs like wrong argument types, missing attributes, and unreachable code before they cause runtime errors.

ty is run via the `astral-sh/ty-pre-commit <https://github.com/astral-sh/ty-pre-commit>`_ hook (which prek uses from the pre-commit hook ecosystem).
Unlike mypy, ty bundles its own typeshed, so the hook requires no ``additional_dependencies`` for standard-library stubs.
Third-party stub packages (e.g. ``types-pyyaml``) are still installed in the project's virtual environment and ty picks them up automatically.

ty configuration resides in the ``[tool.ty]`` section of ``pyproject.toml``.
The key settings are:

- ``environment.python-version``: set to match our ``requires-python`` minimum so ty analyzes against the lowest supported interpreter.
- ``[[tool.ty.overrides]]``: per-path rule overrides (e.g. relaxing ``possibly-unresolved-reference`` to a warning in tests).

ty does **not** warn about missing type annotations (there is no equivalent of mypy's ``disallow_untyped_defs``).
See the `ty FAQ <https://docs.astral.sh/ty/reference/typing-faq/#why-doesnt-ty-warn-about-missing-type-annotations>`_ for the rationale.
To suppress a specific ty diagnostic on a single line, use ``# ty: ignore[rule-name]`` (analogous to mypy's ``# type: ignore[code]``).

Documentation Checking via Interrogate
--------------------------------------

Interrogate is used to ensure that public methods and classes have docstrings embedded within them. This is a good practice, and helps to ensure that the auto-generated documentation gets non-trivial contents. Interrogate is configured in the pyproject.toml.


Code Complexity Checking via Radon/Xenon
----------------------------------------

We are using xenon to enforce a code complexiity measure. We require everything to be above a "C" grade. No custom configuration is needed - that grade level is set in the precommit yaml file.

Code Formatting via Ruff
------------------------

There are many python formatters available. I am of the opinion that __which__ one you choose is less important than __using__ one. I have chosen to use ruff, as it is fast and has a lot of features, and integrates well with prek.

Gherkin Formatting via Gherkin Lint
-----------------------------------

We figured we might as well put some static analysis enforcement on the feature files as well, since those are perhaps the most often read by a broad audience. Again - picking A standard is more important than which one you pick.
