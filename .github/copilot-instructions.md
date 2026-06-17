We use `uv` for managing virtual environments, dependencies, packaging, and running tests.

We practice Behavior Driven Development (BDD) and use pytest for testing. This means that before code is written, we want to make sure of 2 things:
1) There is a test corresponding to the code we are about to write.
2) There is a scenario in a feature file that describes the behavior we want to implement, and is tested by the above test.

Extra documentation, beyond the docstrings and comments in code, can be found in rst files in the docs directory.

We use typer for command line interfaces.

We use sphinx for documentation generation.

We use ty for type checking. ty is configured under `[tool.ty]` in `pyproject.toml`. ty is run via `uv check` for local development. When using `DataFrame.iterrows()`, the index is typed as `Hashable` by the pandas stubs — use `typing.cast(int, idx)` (not `int(idx)`) to assert the correct type to ty. `cast()` is a zero-cost compile-time-only assertion; it does not coerce values at runtime.

We use ruff for code formatting and linting.

We use interrogate to ensure docstring coverage.

We use pre-commit for managing code formatting and linting (leveraging the above tools in that, as well as some others).

As much as possible, we try to put linter and test configuration in the pyproject.toml file, so the exact same configuration can be used in different environments (e.g., local, CI/CD, etc.), and by pre-commit and any IDE the developers may choose.

All "production" code is in the src directory.

All tests are in the tests directory.

We use pytest-bdd for BDD testing.

We favor using pandas/dataframe constructs as much as possible for storing the symbol data in memory - the less we have to DIY the better.

As part of using `uv`, that tends to be the way we run the code, e.g. `uv run src/memtab.py`, or `uv run pytest`.  Do that instead of just `pytest`.

The exception to the above is when running `pre-commit`, which manages its _own_ virtual environment.  So in the case of pre-commit things (like `ruff`, `interrogate`, etc.), we should run `pre-commit run ruff` etc., not just `ruff`, to ensure that the pre-commit hooks are run using pre-commit's environment.

Note: Prefer running `ty` via `uv check` for local development; pre-commit may also run `ty`, but the hook downloads a standalone binary that can require additional SSL trust configuration in some environments.

Basically, between `uv` and `pre-commit`, if you are running a command that depends on python, it should be through those tools, not the native python environment.

We follow [semantic versioning](https://semver.org/) for versioning.

All commits must be signed off with `git commit -s` (or `--signoff`), which appends a `Signed-off-by:` trailer using the committer's name and email. This is required for the [Developer Certificate of Origin (DCO)](https://developercertificate.org/).

For logging, we use the standard library `logging` module, and follow its best practices, unless coming from the command line functions, in which case we use `typer`'s built-in logging support like `echo`.
