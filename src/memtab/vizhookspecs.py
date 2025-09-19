# SPDX-FileCopyrightText: 2025 Eaton Corporation
# SPDX-License-Identifier: MIT
import pluggy

from memtab.memtab import Memtab

hookspecification = pluggy.HookspecMarker("memtab")


class MemtabVisualizerSpec:
    """The hook specification for a memtab visualizer plugin."""

    @hookspecification
    def generate_report(self, memtab: Memtab, filename: str) -> None:
        """Generate the report

        Args:
            memtab (Memtab): the memory table to generate a report against
            filename (str): the filename to write the report to. If None, the plugin can determine its own filename
        """
