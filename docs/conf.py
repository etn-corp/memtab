# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys

project = "Memory Tabulator"
copyright = "2025, Eaton"
author = "Dave VanKampen"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinxcontrib.apidoc",  # for automatic generation of .rst files from Python modules
    "sphinx.ext.autodoc",  # for automatic generation of documentation from docstrings (follows apidoc)
    "sphinx_autodoc_typehints",
    "sphinx_multiversion",
    "sphinx_term.termynal",
    "sphinxcontrib.mermaid",
    "sphinx-jsonschema",
    "sphinxcontrib.images",
    "sphinx_design",  # for cards and grids
]

# region automatic documentation generation configuration
autodoc_typehints_format = "short"
python_use_unqualified_type_names = True

autodoc_mock_imports = ["pluggy", "pandas", "appdirs", "elftools", "referencing", "mdutils", "jsonschema", "git", "click", "typer", "typing_extensions"]

autodoc_default_options = {"members": True, "undoc-members": True}

# this is needed for autodoc to find the sourcecode
sys.path.insert(0, os.path.abspath("../src"))

current_dir = os.path.dirname(__file__)

apidoc_module_dir = "../src"
apidoc_output_dir = current_dir
apidoc_separate_modules = True

# endregion


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


sphinx_term_termynal_dir = "termynal"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
        "versioning.html",
    ],
}


source_path = os.path.normpath(os.path.join(current_dir, "..", "features"))
subprocess.run(
    [
        "sphinx-gherkindoc",
        source_path,
        current_dir,
        "--toc-name",
        "gherkin",
        "--maxtocdepth",
        "4",
    ]
)

# -- Copy schema files to _static folder -------------------------------------

# Create the schemas directory in _static if it doesn't exist
schemas_static_dir = os.path.join(current_dir, "_static", "schemas")
os.makedirs(schemas_static_dir, exist_ok=True)

# Find all schema files in the source directory
schema_files = glob.glob(os.path.join(current_dir, "..", "src", "memtab", "schemas", "*.json"))

# Copy each schema file to the _static/schemas directory
for schema_file in schema_files:
    shutil.copy2(schema_file, schemas_static_dir)


# -- Sphinx-Multiversion Configuration ---------------------------------------
smv_branch_whitelist = r"^main$"  # Only the main branch
smv_tag_whitelist = r"^v?\d+\.\d+\.\d+$"  # Tags in the form X.Y.Z or vX.Y.Z
