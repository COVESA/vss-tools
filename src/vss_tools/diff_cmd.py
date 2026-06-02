# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import json
import sys
from pathlib import Path

import rich_click as click

from vss_tools import log
from vss_tools.diff import diff_folders


@click.command()
@click.option(
    "--previous",
    "-p",
    default=None,
    type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path),
    help="Composed model snapshot used as the basis for the comparison."
    "Omit for first-run mode (all elements treated as ADDED).",
)
@click.option(
    "--current",
    "-c",
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path),
    help="Composed model representing the current version.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Write JSON output to this file instead of stdout.",
)
def cli(previous: Path | None, current: Path, output: Path | None) -> None:
    """
    Diff two vspec compose snapshot folders and produce a modl-compatible diff report.

    Compares signals, structs, units, and quantities across two snapshot
    folders produced by `vspec compose` and reports ADDED, REMOVED, and
    MODIFIED changes as a structured JSON document in the modl adapter IR format.

    When --previous is omitted (first-run mode), every element in --current
    is treated as ADDED and emitted with its complete aspects snapshot.

    Output goes to stdout by default; use --output to write to a file.
    """
    if previous:
        log.info(f"Diffing snapshots: {previous} → {current}")
    else:
        log.info(f"First-run mode: treating all elements in {current} as ADDED")
    result = diff_folders(previous, current)
    out_text = json.dumps(result, indent=2, ensure_ascii=False)

    if output:
        output.write_text(out_text, encoding="utf-8")
        log.info(f"Diff written to {output}")
    else:
        sys.stdout.write(out_text + "\n")
