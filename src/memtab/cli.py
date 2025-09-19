# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
"""The command line interface to the memory tabulator.
We use typer instead of argparse or click because it is the most
ergonomic way to include this code within the scope of a call to pytest.
With argparse, it was a bit more clunky, and typer provides `CliRunner` which
is easier to use."""

import json as js
import logging
import os
from glob import glob
from importlib.metadata import version as vers
from pathlib import Path
from typing import List, Tuple

import click
import pluggy
import typer
from click.core import Context, Parameter
from typing_extensions import Annotated, Optional

from memtab.memtab import Memtab
from memtab.viz import MemtabMarkdownReportSpec
from memtab.vizhookspecs import MemtabVisualizerSpec

# region plugin manager
classname = "memtab"

pm = pluggy.PluginManager(classname)

pm.add_hookspecs(MemtabVisualizerSpec)


def custom_entry_point_load() -> None:
    """
    we have to cheat here if we want to use classes.
    self.pm.load_setuptools_entrypoints only references
    the name, which doesn't work if its a class.
    we need an INSTANCE of the class. So we DIY to get those instances.
    """
    import importlib.metadata

    from pluggy._manager import DistFacade

    for dist in list(importlib.metadata.distributions()):
        for ep in dist.entry_points:
            if (
                ep.group != classname
                # already registered
                or pm.get_plugin(ep.name)
                or pm.is_blocked(ep.name)
            ):
                continue

            plugin_class = ep.load()
            plugin_instance = plugin_class()  # this is where we differ
            pm.register(plugin_instance, name=ep.name)

            # accessing the private member of the plugin manager, _plugin_distinfo,
            # is a fragile way to get the distribution information, but we need to
            # add the class somehow. get_plugins() returns value, not reference.
            pm._plugin_distinfo.append((plugin_class, DistFacade(dist)))


custom_entry_point_load()

pm.register(MemtabMarkdownReportSpec())
# endregion


# region handler for report argument
class ReportType(click.ParamType):  # type: ignore
    """Custom type to parse --report arguments as 'type[:filename]'."""

    name = "report"

    def convert(self, value: str, param: Optional["Parameter"], ctx: Optional["Context"]) -> Tuple[str, str]:
        """Split the input into two parts: report_type and optional filename, using ':' as an optional delimiter."""
        filename = ""
        if ":" in value:
            parts = value.split(":", 1)
            report_type = parts[0]
            filename = parts[1]
        else:
            report_type = value
        return (report_type, filename)


report_type = ReportType()

# endregion


# region helper functions - these may be candidates for being moved to a separate module
def __complete_json_file() -> List[str]:  # pragma: no cover
    return [f for f in os.listdir() if f.endswith(".json")]


def __find_elf_files() -> List[str]:  # pragma: no cover
    """Search the current working directory for .elf files.

    Returns:
        List[str]: the elf files found
    """
    cwd = os.getcwd()
    elf_files = glob(os.path.join(cwd, "*.elf"))
    return elf_files


def __find_config_files() -> List[str]:  # pragma: no cover
    """Search the current working directory for .yml files

    Returns:
        List[str]: the yml files found
    """
    cwd = os.getcwd()
    yml_files = glob(os.path.join(cwd, "*.yml"))
    return yml_files


def __find_report_formats() -> List[str]:  # pragma: no cover
    """List the available plugins according to pluggy

    Returns:
        List[str]: the available report formats
    """
    available_plugins = pm.get_plugins()
    return [plugin.report_name for plugin in available_plugins if hasattr(plugin, "report_name")]


def __gen_reports(reports: Optional[List[ReportType]], tabulator: Memtab) -> None:
    if reports is None:
        return
    for requested_report in reports:
        requested_report_name = requested_report[0]
        requested_report_filename = requested_report[1]
        for plugin in pm.get_plugins():
            if hasattr(plugin, "report_name") and plugin.report_name == requested_report_name:
                plugin.generate_report(memtab=tabulator, filename=requested_report_filename)
                break
        else:
            logging.warning(f"Report type {requested_report_name} not found in {__find_report_formats()}")
            continue


# endregion

# region callbacks


def version_callback(value: bool) -> None:
    """Callback to show the version of memtab"""
    if value:
        print(vers("memtab"))
        raise typer.Exit()


# endregion


# region app
app = typer.Typer()


@app.command()
def memtab(
    elf: Annotated[
        Optional[Path],
        typer.Option(
            help="The elf file to process. Can also be set via the MEMTAB_ELF environment variable, or defined in the yml config file.",
            autocompletion=__find_elf_files,
            envvar="MEMTAB_ELF",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = Path("zephyr.elf"),
    config: Annotated[
        List[Path],
        typer.Option(
            help="The yml config file(s). Can be provided multiple times.",
            autocompletion=__find_config_files,
            envvar="MEMTAB_YML",
        ),
    ] = [Path("memtab.yml")],
    json: Annotated[Path, typer.Option(help="The JSON file to write out to", autocompletion=__complete_json_file, exists=False)] = Path("memtab.json"),
    report: Annotated[
        Optional[List[ReportType]],
        typer.Option(
            click_type=report_type,
            help="Generate report(s) via a plugin. Can be provided multiple times. "
            "If you wish to provide a filename, use a : delimiter, like --report markdown:file.md. "
            "If none is provided, it will use a default filename determined by the plugin itself.",
            autocompletion=__find_report_formats,
        ),
    ] = None,
    check: Annotated[bool, typer.Option(help="Sanity check the data against size, objdump and readelf")] = False,
    cache: Annotated[bool, typer.Option(help="Use cached data")] = True,
    clean: Annotated[bool, typer.Option(help="Clean the cache")] = False,
    map: Annotated[
        Optional[Path],
        typer.Option(
            help="The map file to process",
            envvar="MEMTAB_MAP",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    version: Annotated[Optional[bool], typer.Option(help="Show the version of memtab", callback=version_callback, is_eager=True)] = None,
    project: Annotated[Optional[str], typer.Option(help="The project name")] = None,
) -> None:
    """The main command line entry point for calling the memory tabulator.
    If you want to call memtab from a python app, you should import it
    directly, NOT via this cli method.
    """
    tabulator = Memtab(elf, map_file=map, config=config, cache=cache, check=check, project=project)
    if clean:
        tabulator.clean_cache()
        return
    tabulator.tabulate()

    if json:
        with open(json, "w") as stream:
            js.dump(tabulator.memtab, stream, indent=4)

    __gen_reports(report, tabulator)


# endregion

# region viz-only app

vizapp = typer.Typer()


@vizapp.command()
def memtabviz(
    input: Annotated[
        Optional[Path],
        typer.Option(
            help="The JSON file to process. Can also be set via the MEMTAB_JSON environment variable",
            autocompletion=__complete_json_file,
            envvar="MEMTAB_JSON",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = Path("memtab.json"),
    report: Annotated[
        Optional[List[ReportType]],
        typer.Option(
            click_type=report_type,
            help="Generate report(s) via a plugin. Can be provided multiple times. "
            "If you wish to provide a filename, use a : delimiter, like --report markdown:file.md. "
            "If none is provided, it will use a default filename determined by the plugin itself.",
            autocompletion=__find_report_formats,
        ),
    ] = None,
) -> None:
    """The main command line entry point for calling the memory visual generator.
    If you want to call memtab from a python app, you should import it
    directly, NOT via this cli method.
    """
    tabulator = Memtab()
    if not input:
        typer.echo("No input file specified")
        typer.Exit(1)
    else:
        with open(input, "r") as stream:
            payload = js.load(stream)
        tabulator.memtab = payload
        __gen_reports(report, tabulator)


# endregion

# Note: we don't put a `if __name__ == "__main__":` block here because we only want to have to bother to
# support (and test) the CLI interface defined by the entry point in pyproject.toml.
