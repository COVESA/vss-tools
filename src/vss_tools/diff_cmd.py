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
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path),
    help="Compose snapshot folder representing the previous version.",
)
@click.option(
    "--current",
    "-c",
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path),
    help="Compose snapshot folder representing the current version.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Write JSON output to this file instead of stdout.",
)
def cli(previous: Path, current: Path, output: Path | None) -> None:
    """
    Diff two vspec compose snapshot folders.

    Compares signals, structs, units, and quantities across two snapshot
    folders produced by `vspec compose` and reports ADDED, REMOVED, and
    MODIFIED changes as a structured JSON document.

    Output goes to stdout by default; use --output to write to a file.
    """
    log.info(f"Diffing snapshots: {previous} → {current}")
    result = diff_folders(previous, current)
    out_text = json.dumps(result, indent=2, ensure_ascii=False)

    if output:
        output.write_text(out_text, encoding="utf-8")
        log.info(f"Diff written to {output}")
    else:
        sys.stdout.write(out_text + "\n")
