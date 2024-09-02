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

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode


def get_data(node: VSSNode, with_extra_attributes: bool = True, extended_attributes: tuple[str, ...] = ()):
    data = node.data.as_dict(with_extra_attributes, extended_attributes=extended_attributes)
    if node.uuid:
        data["uuid"] = node.uuid
    if len(node.children) > 0:
        data["children"] = {}
    for child in node.children:
        data["children"][child.name] = get_data(child)
    return data


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.expand_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.types_output_opt
@clo.pretty_print_opt
@clo.extend_all_attributes_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path | None,
    pretty: bool,
    extend_all_attributes: bool,
):
    """
    Export as JSON.
    """
    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        uuid=uuid,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        expand=expand,
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

    with open(output, "w") as f:
        json.dump(signals_data, f, indent=indent, sort_keys=True)
