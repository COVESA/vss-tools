#!/usr/bin/env python3

# Copyright (c) 2016 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert all vspec input files to a single flat YAML file.
#


from pathlib import Path

import rich_click as click
import yaml

import vss_tools.vspec.cli_options as clo
from vss_tools.vspec import load_trees
from vss_tools.vspec.model.vsstree import VSSNode


def export_node(yaml_dict, node, extend_all_attributes, print_uuid, expand):
    node_path = node.qualified_name()

    yaml_dict[node_path] = {}

    yaml_dict[node_path]["type"] = str(node.type.value)

    if node.is_signal() or node.is_property():
        yaml_dict[node_path]["datatype"] = node.get_datatype()

    # many optional attributes are initilized to "" in vsstree.py
    if node.min is not None:
        yaml_dict[node_path]["min"] = node.min
    if node.max is not None:
        yaml_dict[node_path]["max"] = node.max
    if node.allowed != "":
        yaml_dict[node_path]["allowed"] = node.allowed
    if node.default != "":
        yaml_dict[node_path]["default"] = node.default
    if node.deprecation != "":
        yaml_dict[node_path]["deprecation"] = node.deprecation

    # in case of unit or aggregate, the attribute will be missing
    try:
        yaml_dict[node_path]["unit"] = str(node.unit.value)
    except AttributeError:
        pass
    try:
        yaml_dict[node_path]["aggregate"] = node.aggregate
    except AttributeError:
        pass

    yaml_dict[node_path]["description"] = node.description

    if node.comment != "":
        yaml_dict[node_path]["comment"] = node.comment

    if print_uuid:
        yaml_dict[node_path]["uuid"] = node.uuid

    for k, v in node.extended_attributes.items():
        if (
            not extend_all_attributes
            and k not in VSSNode.whitelisted_extended_attributes
        ):
            continue
        yaml_dict[node_path][k] = v

    # Include instance information if we run tool in "no-expand" mode
    if not expand and node.instances is not None:
        yaml_dict[node_path]["instances"] = node.instances

    for child in node.children:
        export_node(yaml_dict, child, extend_all_attributes, print_uuid, expand)


def export_yaml(file_name, content_dict):
    with open(file_name, "w") as f:
        yaml.dump(
            content_dict,
            f,
            default_flow_style=False,
            Dumper=NoAliasDumper,
            sort_keys=True,
            width=1024,
            indent=2,
            encoding="utf-8",
            allow_unicode=True,
        )


# create dumper to remove aliases from output and to add nice new line after each object for a better readability
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()


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
):
    """
    Export as YAML.
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
    )
    data = {}
    export_node(data, tree, extend_all_attributes, uuid, expand)

    if datatype_tree:
        types_data = {}
        export_node(types_data, datatype_tree, extend_all_attributes, uuid, expand)
        if types_output:
            export_yaml(types_output, types_data)
        else:
            data["ComplexDataTypes"] = types_data

    export_yaml(output, data)
