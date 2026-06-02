MCP Server
===========

The Memtab MCP (Model Context Protocol) Server provides an AI-friendly interface to memtab's memory analysis capabilities. This allows AI assistants like GitHub Copilot, Claude Desktop, Cursor, and Zed to analyze ELF file memory usage through standardized MCP tools and resources.

.. note::
   The MCP server feature requires **Python >=3.10** due to the FastMCP dependency, even though core memtab supports Python >=3.9.

Installation
------------

Install memtab with MCP support using the ``mcp`` dependency group:

.. code-block:: bash

   uv pip install memtab[mcp]

Or add it to your project's dependencies:

.. code-block:: bash

   uv add "memtab[mcp]"

If you are just testing MCP in this repository, you can install it with:

.. code-block:: bash

   uv sync --group mcp

How It Works
------------

The MCP server exposes memtab functionality through two types of interfaces:

**Tools** (callable functions):
   * ``get_memory_table`` - Analyzes an ELF file and returns the top 10 symbols by size
   * ``create_memtab_config`` - Generates a starter configuration file

**Resources** (queryable data):
   * ``elf://files`` - Lists all .elf files in the workspace
   * ``elf://file/{path}`` - Returns metadata about a specific ELF file

Environment Variables
---------------------

The MCP server supports these environment variables for configuration:

* ``MEMTAB_ELF`` - Default ELF file path (can use ``file://`` URIs)
* ``MEMTAB_CONFIG`` - Default configuration file path
* ``MEMTAB_SEARCH_DEPTH`` - Maximum directory depth when searching for .elf files
* ``MEMTAB_MCP_DEFAULT_SEARCH_DEPTH`` - Default recursive search depth used by MCP discovery (defaults to ``4``)
* ``MEMTAB_ALLOWED_ROOTS`` - Allowlisted root directories for MCP file access, separated by OS path separator (defaults to current working directory)
* ``MEMTAB_MAX_ELF_BYTES`` - Maximum ELF file size accepted by MCP tools/resources (defaults to ``524288000``)

Security Model
--------------

The memtab MCP server enforces baseline safety checks so each user does not need
to manually secure their local integration:

* MCP file access is restricted to allowlisted roots.
* Recursive ELF discovery is bounded by default.
* ELF files larger than a configured threshold are rejected.

These checks are enforced by the tool itself. Users can tune limits via
environment variables, but safe defaults are active without extra setup.

MCP Versus Copilot Skills
-------------------------

Both MCP and skills are useful, but they solve different problems:

Use MCP when:

* You want one integration that works across MCP-capable hosts.
* You need tool/resource portability beyond VS Code.
* You want structured tool interfaces that other assistants can discover.

Use a Copilot skill when:

* Your primary audience is GitHub Copilot in VS Code.
* You want faster iteration on workflow logic and prompting behavior.
* You want opinionated orchestration around memtab CLI commands.

Recommended approach for most teams: keep MCP for interoperability, and add a
Copilot skill to provide the most productive day-to-day workflow in VS Code.

Configuration Examples
----------------------

GitHub Copilot (VS Code)
~~~~~~~~~~~~~~~~~~~~~~~~~

Create or edit ``.vscode/mcp.json`` in your workspace:

.. literalinclude:: examples/github-copilot-mcp.json
   :language: json

Then restart VS Code or reload the window to activate the MCP server.

Claude Desktop
~~~~~~~~~~~~~~

Add to your Claude Desktop configuration file:

* **macOS**: ``~/Library/Application Support/Claude/claude_desktop_config.json``
* **Windows**: ``%APPDATA%\Claude\claude_desktop_config.json``
* **Linux**: ``~/.config/Claude/claude_desktop_config.json``

.. literalinclude:: examples/claude-desktop-mcp.json
   :language: json

Cursor
~~~~~~

Add to your Cursor configuration:

.. literalinclude:: examples/cursor-mcp.json
   :language: json

Zed
~~~

Add to your Zed settings (``~/.config/zed/settings.json``):

.. literalinclude:: examples/zed-mcp.json
   :language: json

Usage Examples
--------------

Once configured, you can ask your AI assistant questions like:

* "What are the largest symbols in my ELF file?"
* "Analyze the memory usage of my firmware"
* "List all ELF files in this project"
* "Show me memory usage for app.elf"

The AI assistant will use the MCP tools to automatically:

1. Discover ELF files in your workspace
2. Find or prompt for a memtab configuration file
3. Run memory analysis using memtab
4. Return formatted results

Running the Server Manually
----------------------------

For testing or debugging in _this_ repository, you can run the MCP server directly:

.. code-block:: bash

   # Using uv
   uv run memtab_mcp

   # Or with environment variables
   MEMTAB_ELF=/path/to/app.elf MEMTAB_CONFIG=/path/to/config.yml memtab_mcp

   # For development in this repository, use uv:
   uv run memtab_mcp

The server communicates via stdio using the MCP protocol.


Troubleshooting
---------------

**Python version mismatch**
   If you see import errors related to FastMCP, ensure you're using Python 3.10 or later:

   .. code-block:: bash

      python --version  # Should be 3.10+

**MCP server not appearing**
   * Verify the configuration file is in the correct location for your AI host
   * Check that ``memtab_mcp`` is in your PATH (``which memtab_mcp``)
   * Restart your AI host application after configuration changes

**ELF file not found**
   * Set ``MEMTAB_ELF`` environment variable in the configuration
   * Or place your .elf file in the workspace root
   * Use ``MEMTAB_SEARCH_DEPTH`` to control recursive search depth

See Also
--------

* :doc:`usage` - Core memtab usage and configuration
* :doc:`architecture` - Understanding memtab's design
* `Model Context Protocol Specification <https://modelcontextprotocol.io/>`_
