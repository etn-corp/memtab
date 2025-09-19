##########
Versioning
##########

Versioning is an important aspect of software development. It helps users and developers keep track of changes, improvements, and bug fixes over time. A well-defined versioning strategy also helps with dependency management, compatibility checks, and release management.

*******************
Versioning Strategy
*******************

In general, this project will try to follow `semantic versioning <https://semver.org/>`_. We say "in general" because at the end of the day, all versioning strategies come down to human judgment.

Nonetheless, we will try to follow the following guidelines:

#. **Major version**: incremented for incompatible API changes. This includes changes to the command line interface (CLI) that break backward compatibility.
#. **Minor version**: incremented for new functionality that is backward compatible. This includes new features, new command line arguments, and new output formats.
#. **Patch version**: incremented for backward-compatible bug fixes. This includes fixing incorrect behavior, improving performance, and improving documentation. It does not include new features or new command line arguments.


We looked at some tools built to help automate this process, but they were determined to not meet our needs as well as these. Some other options we considered were:

* `bump2version <https://pypi.org/project/bump2version/>`_
  * This seemed focused on propagating changes across multiple checked-in files.  Our goal was that we really only have the number written down in one place, so there shouldn't be a need to propagate anything.
* `versioneer <https://pypi.org/project/versioneer/>`_
  * This creates a custom ``_version.py``, which to us just seems to introduce yet another possible source of truth (see below).

***********************
Single Source of Truth
***********************

One key challenge to keep in mind when managing version numbers is ensuring that the version number is consistent across all the places it is referenced.
This is important because if the version number is not consistent, it can lead to confusion for users and developers, and worse, inconsistent dependency trees. This includes keeping *at least* all of the following consistent:

#. The version shown by pip (e.g., when you run ``pip show memtab`` or ``pip freeze``).

  * This one is likely the most important, in the end, because it is what is used for dependency management.

#. The Python package version (e.g., in the ``pyproject.toml`` file).
#. The version shown in the Python package itself (e.g., in the ``__init__.py`` file, if you choose to put it there).
#. The version shown by importlib.metadata (e.g., when you run ``importlib.metadata.version("memtab")``).
#. The version displayed in the command line interface (CLI) when the user runs ``memtab --version``.
#. The version displayed in the documentation (e.g., in the header of the documentation pages).
#. The version used in the release notes and changelog (if any).
#. The version used in the Git tags for tracking and releases.

Some documentation from the python packaging guidelines on single-sourcing can be found `here <https://packaging.python.org/en/latest/discussions/single-source-version/>`_.

For this project, the **single source of truth** is the ``pyproject.toml`` file. Specifically, the ``version`` field in the ``[project]`` section. All other version references should be derived from this single source.

To make things easier and less error-prone, this derivation is enforced via a combination of the following:

* The command line will use importlib.metadata to get the version number when the user runs ``memtab --version``. This blends a few of the above together to reduce variables.
* We won't put anything in the ``__init__.py``
* When the ``main`` branch is updated, a github action will be used to apply the version number to the repository as a release + tag if it does not exist.
* When a tag is created, new documentation will be generated containing the new version (and all previous versions). This way, developers only need to update the ``pyproject.toml`` version, they don't *also* have to manually create a git tag.

**************************************
Supporting Versioning in Documentation
**************************************

One additional change that comes along with adding a versioning strategy is that we need to ensure that the documentation is also versioned. This is important because:

#. Different versions of the software may have different features, command line arguments, and output formats.
#. Users may want to refer to the documentation for a specific version of the software, especially if they are using an older version.

To that end, as we add a versioning notion to this repository, we need to update the documentation generation workflows to generate documentation for all previous versions of the package. That way, every time the documentation is re-deployed, it will include all historical versions as well as the latest.
The basic process there is simply to repeat the documentation generation process for each version. This can be done by:
#. Using a script to loop through all the versions we want to generate documentation for (checking out the repository to that version, via git tags).
#. Running the documentation generation command (e.g., Sphinx) for each version.
#. By leveraging `sphinx-multiversion <https://sphinx-contrib.github.io/multiversion/main/quickstart.html/>`_, we can generate a versioned documentation site that allows users to easily switch between all historical versions.
