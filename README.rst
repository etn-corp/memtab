memtab
======

.. warning::
   **For detailed documentation, please view the documentation web page:** https://etn-corp.github.io/memtab/


``memtab`` is a Python-based project that provides both a command line interface (CLI) and a Python library. It is designed to produce both machine and human-readable reports from binary files in the ELF (Executable and Linkable Format) format.

For more information on the ELF file format, please refer to the `Wikipedia article on ELF <https://en.wikipedia.org/wiki/Executable_and_Linkable_Format>`_.

Features
--------

- Command Line Interface (CLI)
- Python library
- Generates machine-readable reports
- Generates human-readable reports

Installation
------------

To install ``memtab``, you can use ``pip``:

.. code-block:: sh

   pip install memtab

You can also install it directly from git if desired:

.. code-block:: sh

   pip install git+https://github.com/etn-corp/memtab.git

Usage
-----

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

To use the CLI, run:

.. code-block:: sh

   memtab --elf <path-to-elf-file> --config <path-to-yml-file>

Python Library
~~~~~~~~~~~~~~

To use the Python library:

.. code-block:: python

   import memtab

   tabulator = Memtab(elf_file, [config])
   report = tabulator.tabulate()

   print(report)  # this is a pandas dataframe at this point

GitHub Action
~~~~~~~~~~~~~~

To use this as a GitHub Action:

.. code-block:: yaml

  - name: Memtab
    uses: etn-corp/memtab@main
    with:
        sdk_path: [YOUR_SDK_HERE]
        elf: ${{ github.workspace }}\source\build\zephyr\zephyr.elf

The action will generate the markdown output (using the `--md` argument) and upload that markdown as a step summary.

Developing
----------

This project is managed using ``uv``. For more information, refer to `Astral's page on uv <https://astral.sh/uv/>`_.

Common Commands
~~~~~~~~~~~~~~~

- ``uv sync``: Sync your development environment with the project dependencies.
- ``uv run <command>``: Run a command within the project's virtual environment.
- ``uv build``: generate a pip installable wheel or sdist file in the ``dist/`` directory.

Running Tests
~~~~~~~~~~~~~

To run tests, use ``uv`` with coverage:

.. code-block:: sh

   uv run coverage run -m pytest

Pre-commit Hooks
~~~~~~~~~~~~~~~~

We use ``pre-commit`` to ensure code quality and consistency. After cloning the project, install the pre-commit hooks by running:

.. code-block:: sh

   pre-commit install

For more information on ``pre-commit``, visit the `pre-commit website <https://pre-commit.com/>`_.

We also have a GitHub Action that runs ``pre-commit`` checks on every push and pull request, so you can rely on that if you prefer not to install ``pre-commit`` locally.

Contribution Guidelines
-----------------------

We welcome contributions! Please follow these guidelines:

#. Fork the repository.
#. Create a new branch (``git checkout -b feature-branch``).
#. Make your changes.
#. Commit your changes (``git commit -am 'Add new feature'``).
#. Push to the branch (``git push origin feature-branch``).
#. Create a new Pull Request.

Reporting Issues
----------------

If you encounter any issues, please report them on the `GitHub Issues <https://github.com/etn-corp/memtab/issues>`_ page.

Generating Documentation
------------------------

To generate documentation, use ``Sphinx``:

.. code-block:: sh

   sphinx-build docs docs/_build/html

Or, if you have ``poe`` installed, you can run:

.. code-block:: sh

   poe docs

License
-------

This project is licensed under the MIT License. See the `LICENSE file <https://github.com/etn-corp/memtab/blob/main/LICENSE>`_ for more information.
