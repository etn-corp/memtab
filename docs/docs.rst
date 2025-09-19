Documentation
=============


Sphinx Autodocs
---------------

This project uses `Sphinx <https://www.sphinx-doc.org/>`_ to generate documentation. You can think of sphinx as a more modern doxygen for python. The documentation is written in reStructuredText (reST) format and is located in the `docs` directory.
The documentation is generated using the `sphinx-build` command, which is part of the Sphinx package. The generated documentation is then uploaded to the `gh-pages` branch of the repository.
When it is generated in github, the documentation is hosted on `GitHub Pages <https://pages.github.com/>`_ and can be accessed at `https://etn-corp.github.io/memtab/`.


The project uses the `sphinx.ext.autodoc` and `sphinx_autodoc_typehints` extensions to automatically generate documentation from the code.


The `sphinx.ext.autodoc` extension is used to automatically fill the source code documentation from the docstrings at module and public function level. Note that we currently exclude private methods (those prepended with a `__`).

The `sphinx_autodoc_typehints` extension is used to automatically shorten the generated documentation, specifically the typehints. Without this extension, type hints would come in as fully qualified, which decreases their readability.


Docstrings via Interrogate
--------------------------

This projects uses `Interrogate <https://interrogate.readthedocs.io/en/latest/>`_ to enforce the addition of docstrings to python code. It does this via the interrogate settings in the pyproject.toml file, as well as the interrogate precommit hook in the `.precommit-config.yaml` file.

This will make it so if you add a public method, or a module, or class, without the appropriate docstrings, the precommit hook will fail, and you will not be able to commit your code, or at least not get it through PR. More on this can be found in :doc:`precommit`.

Generating Documentation
------------------------
Since the sphinx project has already been created and checked in (thanks to sphinx-quickstart), the only thing left to do is to run the appropriate `sphinx` command. This command will generate the documentation in the `docs/_build` directory.
The command to generate the documentation is:

.. code-block:: console

   (.venv) $ invoke docs


At this point, you will have a docs/_build/html directory with the generated documentation. In a separate terminal, you can run this:

.. code-block:: console

   $ python -m http.server 8000 --directory docs/_build/html

and then just leave that terminal open. You can repeatedly regenerate the documentation, and use this page to view them as you are editing.

Note for simplicity, you can also add a ``--serve`` argument to the ``invoke docs`` call, and it will do the above step for you.


Why Require Documentation?
--------------------------

There is a broad spectrum of opinions around code documentation.
On one end of the spectrum, you have the "self-documenting code" camp, which believes that code should be written in such a way that it is self-explanatory.
On the other end, you have the "documentation is king" camp, where you almost cannot have too much documentation, and every line could benefit from explanatory text.

As with so many things, the pragmatic view, taken by this project, falls in between the extremes. We require that all public methods, classes, and modules have docstrings. This is enforced by the interrogate precommit hook (described above) and published by sphinx (also described above).

This is an attempt to ensure that the documentation is kept up to date with the code. While not the *MOST* important part of code quality, documentation IS a contributing factor, for the following reasons:
#. It can aid in on-boarding new developers to help contribute more quickly.
#. It helps "keep developers honest" by giving them a reason to think about *why* a method exists, and how it fits into the larger picture of the class, module, package, etc.
#. the allowance for internal methods and init methods to be uncommented matches a "behavior driven development" approach, where the emphasis is on external facing functionality, and the internal details are less critical.
By not requiring docstrings on internal methods, it makes it easier to change those, as long as the external behavior (validated by BDD tests) remain passing.
