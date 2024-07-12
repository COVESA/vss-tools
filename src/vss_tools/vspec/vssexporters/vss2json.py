#!/usr/bin/env python3

# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to JSON

from vss_tools.vspec.model.vsstree import VSSNode
import json
import rich_click as click
import vss_tools.vspec.cli_options as clo
from vss_tools.vspec.vssexporters.utils import get_trees
from pathlib import Path
from typing import Dict, Any
from vss_tools import log


def export_node(
    json_dict, node, print_uuid, all_extended_attributes: bool, expand: bool
):
    json_dict[node.name] = {}

    if node.is_signal() or node.is_property():
        json_dict[node.name]["datatype"] = node.data_type_str

    json_dict[node.name]["type"] = str(node.type.value)

    # many optional attributes are initilized to "" in vsstree.py
    if node.min is not None:
        json_dict[node.name]["min"] = node.min
    if node.max is not None:
        json_dict[node.name]["max"] = node.max
    if node.allowed != "":
        json_dict[node.name]["allowed"] = node.allowed
    if node.default != "":
        json_dict[node.name]["default"] = node.default
    if node.deprecation != "":
        json_dict[node.name]["deprecation"] = node.deprecation

    # in case of unit or aggregate, the attribute will be missing
    try:
        json_dict[node.name]["unit"] = str(node.unit.value)
    except AttributeError:
        pass
    try:
        json_dict[node.name]["aggregate"] = node.aggregate
    except AttributeError:
        pass

    json_dict[node.name]["description"] = node.description
    if node.comment != "":
        json_dict[node.name]["comment"] = node.comment

    if print_uuid:
        json_dict[node.name]["uuid"] = node.uuid

    for k, v in node.extended_attributes.items():
        if (
            not all_extended_attributes
            and k not in VSSNode.whitelisted_extended_attributes
        ):
            continue
        json_dict[node.name][k] = v

    # Include instance information if we run tool in "no-expand" mode
    if not expand and node.instances is not None:
        json_dict[node.name]["instances"] = node.instances

    # Might be better to not generate child dict, if there are no children
    # if node.type == VSSType.BRANCH and len(node.children) != 0:
    #    json_dict[node.name]["children"]={}

    # But old JSON code always generates children, so lets do so to
    if node.is_branch() or node.is_struct():
        json_dict[node.name]["children"] = {}

    for child in node.children:
        export_node(
            json_dict[node.name]["children"],
            child,
            print_uuid,
            all_extended_attributes,
            expand,
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
    tree, datatype_tree = get_trees(
        include_dirs,
        aborts,
        strict,
        extended_attributes,
        uuid,
        quantities,
        vspec,
        units,
        types,
        types_output,
        overlays,
        expand,
    )
    log.info("Generating JSON output...")
    indent = None
    if pretty:
        log.info("Serializing pretty JSON...")
        indent = 2
    else:
        log.info("Serializing compact JSON...")

    signals_json_dict: Dict[str, Any] = {}
    export_node(signals_json_dict, tree, uuid, extend_all_attributes, expand)

    if datatype_tree:
        data_types_json_dict: Dict[str, Any] = {}
        export_node(
            data_types_json_dict, datatype_tree, uuid, extend_all_attributes, expand
        )
        if types_output:
            log.info("Adding custom data types to signal dictionary")
            signals_json_dict["ComplexDataTypes"] = data_types_json_dict
        else:
            with open(types_output, "w") as f:
                json.dump(data_types_json_dict, f, indent=indent, sort_keys=True)

    with open(output, "w") as f:
        json.dump(signals_json_dict, f, indent=indent, sort_keys=True)
