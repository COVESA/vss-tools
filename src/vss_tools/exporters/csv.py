# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to CSV

import csv
from pathlib import Path
from typing import Any

import pandas as pd
import rich_click as click
from anytree import PreOrderIter  # type: ignore[import]

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.exporters.stats_utils import process_piechart_stats, process_sankey_stats
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode
from vss_tools.utils.misc import getattr_nn


def get_header(entry_type: str, with_instance_column: bool, extended_attributes: tuple[str, ...] = ()) -> list[str]:
    row = [
        entry_type,
        "Type",
        "DataType",
        "Deprecated",
        "Unit",
        "Min",
        "Max",
        "Desc",
        "Comment",
        "Allowed",
        "Default",
    ]
    if with_instance_column:
        row.append("Instances")

    row.extend(extended_attributes)

    return row


def add_rows(
    rows: list[list[Any]], root: VSSNode, with_instance_column: bool, extended_attributes: tuple[str, ...] = ()
) -> None:
    node: VSSNode
    for node in PreOrderIter(root):
        data = node.get_vss_data()
        row = [
            node.get_fqn(),
            data.type.value,
            getattr_nn(data, "datatype", ""),
            getattr_nn(data, "deprecation", ""),
            getattr_nn(data, "unit", ""),
            getattr_nn(data, "min", ""),
            getattr_nn(data, "max", ""),
            data.description,
            getattr_nn(data, "comment", ""),
            getattr_nn(data, "allowed", ""),
            getattr_nn(data, "default", ""),
        ]
        if with_instance_column:
            row.append(getattr_nn(data, "instances", ""))

        for attr in extended_attributes:
            row.append(getattr_nn(data, attr, ""))
        rows.append(row)


def write_csv(rows: list[list[Any]], output: Path):
    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


@click.command()
@clo.vspec_opt
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output file (optional when using stats options).",
)
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.expand_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.types_output_opt
@click.option(
    "--stats-sankey",
    type=click.Path(path_type=Path),
    help="Generate Sankey diagram statistics into following CSV file (automatically applies --no-expand)",
)
@click.option(
    "--stats-piechart",
    type=click.Path(path_type=Path),
    help="Generate pie chart statistics into following CSV file (automatically applies --no-expand)",
)
@click.option(
    "--stats-old-piechart",
    type=click.Path(exists=True, path_type=Path),
    help="Path to existing chart data for pie chart stats",
)
def cli(
    vspec: Path,
    output: Path | None,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path,
    stats_sankey: Path | None,
    stats_piechart: Path | None,
    stats_old_piechart: Path | None,
):
    """
    Export as CSV.
    """
    # Validate that either output or stats options are provided
    stats_requested = stats_sankey or stats_piechart
    if not output and not stats_requested:
        raise click.ClickException(
            "Either --output or one of the stats options (--stats-sankey, --stats-piechart) must be provided"
        )

    if stats_piechart and not stats_old_piechart:
        raise click.ClickException("--stats-old-piechart is required when using --stats-piechart")

    if stats_requested and expand:
        log.warning(
            "Stats processing requires --no-expand option. Automatically setting expand=False for stats generation."
        )
        expand = False

    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        expand=expand,
    )
    log.info("Generating CSV output...")

    generic_entry = datatype_tree and not types_output
    with_instance_column = not expand

    entry_type = "Node" if generic_entry else "Signal"
    rows = [get_header(entry_type, with_instance_column, extended_attributes)]
    add_rows(rows, tree, with_instance_column, extended_attributes)
    if generic_entry and datatype_tree:
        add_rows(rows, datatype_tree, with_instance_column)

    # Only write main CSV output if output path is provided
    if output:
        write_csv(rows, output)

    if not generic_entry and datatype_tree and types_output:
        types_rows = [get_header("Node", with_instance_column)]
        add_rows(types_rows, datatype_tree, with_instance_column)
        write_csv(types_rows, types_output)

    if stats_requested:
        df = pd.DataFrame(rows[1:], columns=rows[0])

        if stats_sankey:
            log.info("Processing Sankey statistics...")
            process_sankey_stats(df.copy(), stats_sankey)

        if stats_piechart:
            log.info("Processing pie chart statistics...")
            assert stats_old_piechart is not None
            process_piechart_stats(df.copy(), stats_piechart, stats_old_piechart)
