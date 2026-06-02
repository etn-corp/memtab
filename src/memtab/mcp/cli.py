# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""Command line interface for the Memtab MCP Server.

We use typer instead of argparse or click because it is the most
ergonomic way to include this code within the scope of a call to pytest.
With argparse, it was a bit more clunky, and typer provides `CliRunner` which
is easier to use.
"""

import sys

import typer

try:
    from memtab.mcp.server import mcp
except ImportError:
    print(
        "Error: MCP server dependencies not installed.\nPlease install with: uv sync --group mcp\nNote: MCP functionality requires Python >=3.10",
        file=sys.stderr,
    )
    sys.exit(1)

app = typer.Typer()


@app.command()
def main() -> None:
    """The main command line entry point for calling the Memtab MCP Server.

    If you want to call memtab_mcp_server from a python app, you should import it
    directly, NOT via this cli method.
    """
    # Start the MCP server
    mcp.run()


# Note: we don't put a `if __name__ == "__main__":` block here because we only want to have to bother to
# support (and test) the CLI interface defined by the entry point in pyproject.toml.
