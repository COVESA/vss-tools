#!/usr/bin/env python3

# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to JSON

from pathlib import Path
from typing import Any

import rich_click as click

import vss_tools.vspec.cli_options as clo
from vss_tools.vspec import load_trees
from vss_tools.vspec.model.vsstree import VSSNode
from vss_tools.vspec.utils.files import write_json


def export_node(
    data: dict[str, Any],
    node: VSSNode,
    extend_all_attributes: bool,
    uuid: bool,
    expand: bool,
):
    data[node.name] = {}

    if node.is_signal() or node.is_property():
        data[node.name]["datatype"] = node.data_type_str

    data[node.name]["type"] = str(node.type.value)

    # many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        data[node.name]["min"] = node.min
    if node.max != "":
        data[node.name]["max"] = node.max
    if node.allowed != "":
        data[node.name]["allowed"] = node.allowed
    if node.default != "":
        data[node.name]["default"] = node.default
    if node.deprecation != "":
        data[node.name]["deprecation"] = node.deprecation

    # in case of unit or aggregate, the attribute will be missing
    try:
        data[node.name]["unit"] = str(node.unit.value)
    except AttributeError:
        pass
    try:
        data[node.name]["aggregate"] = node.aggregate
    except AttributeError:
        pass

    data[node.name]["description"] = node.description
    if node.comment != "":
        data[node.name]["comment"] = node.comment

    if uuid:
        data[node.name]["uuid"] = node.uuid

    for k, v in node.extended_attributes.items():
        if (
            not extend_all_attributes
            and k not in VSSNode.whitelisted_extended_attributes
        ):
            continue
        data[node.name][k] = v

    # Include instance information if we run tool in "no-expand" mode
    if not expand and node.instances is not None:
        data[node.name]["instances"] = node.instances

    # But old JSON code always generates children, so lets do so to
    if node.is_branch() or node.is_struct():
        data[node.name]["children"] = {}

    for child in node.children:
        export_node(
            data[node.name]["children"], child, extend_all_attributes, uuid, expand
        )


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
@clo.extend_all_attributes_opt
@clo.pretty_print_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: str,
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path,
    extend_all_attributes: bool,
    pretty: bool,
):
    """
    Export as JSON.
    """
    tree, datatype_tree = load_trees(
        vspec,
        include_dirs,
        extended_attributes,
        quantities,
        units,
        overlays,
        types,
        aborts,
        strict,
        expand,
    )
    data = {}
    indent = 2 if pretty else None
    export_node(data, tree, extend_all_attributes, uuid, expand)
    if datatype_tree:
        types_data = {}
        export_node(types_data, datatype_tree, extend_all_attributes, uuid, expand)
        if types_output:
            types_output.parent.mkdir(exist_ok=True, parents=True)
            write_json(types_data, types_output, indent)
        else:
            data["ComplexDataTypes"] = types_data
    write_json(data, output, indent)
