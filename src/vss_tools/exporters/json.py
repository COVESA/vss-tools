# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to JSON

import json
from pathlib import Path
from typing import Any

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.exporters.stats_utils import process_radial_stats
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode


def get_data(node: VSSNode, with_extra_attributes: bool = True, extended_attributes: tuple[str, ...] = ()):
    data = node.data.as_dict(with_extra_attributes, extended_attributes=extended_attributes)
    if len(node.children) > 0:
        data["children"] = {}
    for child in node.children:
        data["children"][child.name] = get_data(child)
    return data


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
@clo.pretty_print_opt
@clo.extend_all_attributes_opt
@clo.strict_exceptions_opt
@click.option(
    "--stats-radial",
    type=click.Path(path_type=Path),
    default=None,
    help="Generate radial tree statistics into following JSON file",
)
@click.pass_context
def cli(
    ctx,
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
    types_output: Path | None,
    pretty: bool,
    extend_all_attributes: bool,
    stats_radial: Path | None,
    strict_exceptions: Path | None,
):
    """
    Export as JSON.
    """
    # Validate that either output or stats options are provided
    if not output and not stats_radial:
        raise click.ClickException("Either --output or --stats-radial must be provided")

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
        strict_exceptions_file=strict_exceptions,
    )
    log.info("Generating JSON output...")
    indent = None
    if pretty:
        indent = 2

    signals_data = {tree.name: get_data(tree, extend_all_attributes, extended_attributes)}

    if datatype_tree:
        types_data: dict[str, Any] = {datatype_tree.name: get_data(datatype_tree, extend_all_attributes)}
        if not types_output:
            log.info("Adding custom data types to signal dictionary")
            signals_data["ComplexDataTypes"] = types_data
        else:
            with open(types_output, "w") as f:
                json.dump(types_data, f, indent=indent, sort_keys=True)

    # Only write main JSON output if output path is provided
    if output:
        with open(output, "w") as f:
            json.dump(signals_data, f, indent=indent, sort_keys=True)

    # Generate radial statistics if requested
    if stats_radial:
        log.info("Processing radial statistics...")
        process_radial_stats(signals_data, stats_radial)
