Testing
=======

All of the testing on this project is run through pytest-bdd.

The feature files are in the `features` directory.

The tests that implement those features are in the `tests` directory.

The tests are run using the `pytest` command.  As with all other aspects of this project, you can most easily invoke tests through `uv`.

.. code-block:: console

   $ uv run pytest

Note this is what the pytest github action does.

Some helpful pytest arguments:

* `-x` - stop after first failure
* `--lf` - run only the last failed tests
* `-v` - verbose output
* `-s` - show print statements
* `-k` - run only tests that match the given expression
