#
# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
#
# Convert vspec tree compatible JSON schema

import json
from pathlib import Path
from typing import Any, Dict

import rich_click as click

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.model import VSSDataBranch, VSSDataDatatype, VSSDataStruct
from vss_tools.vspec.tree import VSSNode

type_map = {
    "int8": "integer",
    "uint8": "integer",
    "int16": "integer",
    "uint16": "integer",
    "int32": "integer",
    "uint32": "integer",
    "int64": "integer",
    "uint64": "integer",
    "boolean": "boolean",
    "float": "number",
    "double": "number",
    "string": "string",
    "int8[]": "array",
    "uint8[]": "array",
    "int16[]": "array",
    "uint16[]": "array",
    "int32[]": "array",
    "uint32[]": "array",
    "int64[]": "array",
    "uint64[]": "array",
    "boolean[]": "array",
    "float[]": "array",
    "double[]": "array",
    "string[]": "array",
}


def export_node(
    json_dict,
    node: VSSNode,
    print_uuid: bool,
    all_extended_attributes: bool,
    no_additional_properties: bool,
    require_all_properties: bool,
):
    """Preparing nodes for JSON schema output."""
    # keyword with X- sign are left for extensions and they are not part of official JSON schema
    data = node.get_vss_data()
    json_dict[node.name] = {
        "description": data.description,
    }

    if isinstance(data, VSSDataDatatype):
        json_dict[node.name]["type"] = type_map[data.datatype]

    min = getattr(data, "min", None)
    if min is not None:
        json_dict[node.name]["minimum"] = min

    max = getattr(data, "max", None)
    if max is not None:
        json_dict[node.name]["maximum"] = max

    allowed = getattr(data, "allowed", None)
    if allowed:
        json_dict[node.name]["enum"] = allowed

    default = getattr(data, "default", None)
    if default:
        json_dict[node.name]["default"] = default

    if isinstance(data, VSSDataStruct):
        json_dict[node.name]["type"] = "object"

    if all_extended_attributes:
        json_dict[node.name]["x-VSStype"] = data.type.value
        datatype = getattr(data, "datatype", None)
        if datatype:
            json_dict[node.name]["x-datatype"] = datatype
        if data.deprecation:
            json_dict[node.name]["x-deprecation"] = data.deprecation

        # in case of unit or aggregate, the attribute will be missing
        unit = getattr(data, "unit", None)
        if unit:
            json_dict[node.name]["x-unit"] = unit

        aggregate = getattr(data, "aggregate", None)
        if aggregate:
            json_dict[node.name]["x-aggregate"] = aggregate
            if aggregate:
                json_dict[node.name]["type"] = "object"

        if data.comment:
            json_dict[node.name]["x-comment"] = data.comment

        if print_uuid:
            json_dict[node.name]["x-uuid"] = node.uuid

    for field in data.get_extra_attributes():
        json_dict[node.name][field] = getattr(data, field)

    # Generate child nodes
    if isinstance(data, VSSDataBranch) or isinstance(node.data, VSSDataStruct):
        if no_additional_properties:
            json_dict[node.name]["additionalProperties"] = False
        json_dict[node.name]["properties"] = {}
        if require_all_properties:
            json_dict[node.name]["required"] = [child.name for child in node.children]
        for child in node.children:
            export_node(
                json_dict[node.name]["properties"],
                child,
                print_uuid,
                all_extended_attributes,
                no_additional_properties,
                require_all_properties,
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
@clo.extend_all_attributes_opt
@clo.pretty_print_opt
@click.option(
    "--no-additional-properties",
    is_flag=True,
    help="Do not allow properties not defined in VSS tree",
)
@click.option(
    "--require-all-properties",
    is_flag=True,
    help="Required all elements defined in VSS tree for a valid object",
)
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
    extend_all_attributes: bool,
    pretty: bool,
    no_additional_properties: bool,
    require_all_properties: bool,
):
    """
    Export as a jsonschema.
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
    log.info("Generating JSON schema...")
    indent = None
    if pretty:
        log.info("Serializing pretty JSON schema...")
        indent = 2

    signals_json_schema: Dict[str, Any] = {}
    export_node(
        signals_json_schema,
        tree,
        uuid,
        extend_all_attributes,
        no_additional_properties,
        require_all_properties,
    )

    # Add data types to the schema
    if datatype_tree is not None:
        data_types_json_schema: Dict[str, Any] = {}
        export_node(
            data_types_json_schema,
            datatype_tree,
            uuid,
            extend_all_attributes,
            no_additional_properties,
            require_all_properties,
        )
        if extend_all_attributes:
            signals_json_schema["x-ComplexDataTypes"] = data_types_json_schema

    # VSS models only have one root, so there should only be one
    # key in the dict
    assert len(signals_json_schema.keys()) == 1
    top_node_name = list(signals_json_schema.keys())[0]
    signals_json_schema = signals_json_schema.pop(top_node_name)

    json_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": top_node_name,
        "type": "object",
        **signals_json_schema,
    }
    with open(output, "w", encoding="utf-8") as output_file:
        json.dump(json_schema, output_file, indent=indent, sort_keys=False)
