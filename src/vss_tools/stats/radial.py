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
@clo.output_required_opt
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
@click.pass_context
def cli(
    ctx,
    vspec: Path,
    output: Path,
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
):
    """
    Export JSON Data for Radial Tree.
    """

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
    log.info("Generating JSON output...")

    signals_data = {tree.name: get_data(tree, extend_all_attributes, extended_attributes)}

    if datatype_tree:
        types_data: dict[str, Any] = {datatype_tree.name: get_data(datatype_tree, extend_all_attributes)}
        if not types_output:
            log.info("Adding custom data types to signal dictionary")
            signals_data["ComplexDataTypes"] = types_data
        else:
            with open(types_output, "w") as f:
                json.dump(types_data, f, indent=2, sort_keys=True)

    def build_json_structure(obj, parent_name=None):
        result = []
        for key, value in obj.items():
            item = {"name": key}
            if "children" in value:
                item["children"] = build_json_structure(value["children"], key)
            else:
                for prop, prop_value in value.items():
                    if prop != "children":
                        item[prop] = prop_value
            result.append(item)

        result.sort(key=lambda x: ("children" not in x, x.get("type", "")))
        return result

    new_data = {
        "name": "Vehicle",
        "type": "Vehicle",
        "children": build_json_structure(signals_data["Vehicle"]["children"]),
    }

    with open(output, "w") as f:
        json.dump(new_data, f, indent=2)
