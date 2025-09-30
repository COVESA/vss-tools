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
from typing import Any

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.datatypes import Datatypes, is_array, resolve_datatype
from vss_tools.main import get_trees
from vss_tools.model import VSSDataBranch, VSSDataDatatype
from vss_tools.tree import VSSNode


class JsonSchemaExporterException(Exception):
    pass


type_map = {
    Datatypes.INT8[0]: ("integer", -128, 127),
    Datatypes.UINT8[0]: ("integer", 0, 255),
    Datatypes.INT16[0]: ("integer", -32768, 32767),
    Datatypes.UINT16[0]: ("integer", 0, 65535),
    Datatypes.INT32[0]: ("integer", -2147483648, 2147483647),
    Datatypes.UINT32[0]: ("integer", 0, 4294967295),
    Datatypes.INT64[0]: ("integer",),
    Datatypes.UINT64[0]: ("integer",),
    Datatypes.FLOAT[0]: ("number",),
    Datatypes.DOUBLE[0]: ("number",),
    Datatypes.NUMERIC[0]: ("number",),
    Datatypes.BOOLEAN[0]: ("boolean",),
    Datatypes.STRING[0]: ("string",),
}


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

    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": tree.name}

    add_node(schema, tree, datatype_tree, no_additional_properties, require_all_properties, extend_all_attributes)

    with open(output, "w", encoding="utf-8") as output_file:
        json.dump(schema, output_file, indent=indent, sort_keys=False)


def find_type_node(datatype_tree: VSSNode | None, fqn: str) -> VSSNode | None:
    if not datatype_tree:
        return None
    return datatype_tree.get_node_with_fqn(fqn)


def add_x_attributes(schema: dict[str, Any], node: VSSNode) -> None:
    data = node.get_vss_data()
    schema["x-VSStype"] = data.type.value
    if isinstance(node.data, VSSDataDatatype):
        schema["x-datatype"] = node.data.datatype
        if node.data.unit:
            schema["x-unit"] = node.data.unit
    if data.deprecation:
        schema["x-deprecation"] = data.deprecation
    if isinstance(node.data, VSSDataBranch):
        schema["x-aggregate"] = node.data.aggregate
    if data.comment:
        schema["x-comment"] = data.comment


def add_node(
    schema: dict[str, Any],
    node: VSSNode,
    dtree: VSSNode | None,
    no_additional_props: bool,
    require_all_properties: bool,
    extend_all_attributes: bool,
) -> None:
    schema["type"] = "object"
    schema["description"] = node.get_vss_data().description
    if extend_all_attributes:
        add_x_attributes(schema, node)
    if isinstance(node.data, VSSDataDatatype):
        ref = schema
        if is_array(node.data.datatype):
            schema["type"] = "array"
            schema["items"] = {}
            ref = schema["items"]
        datatype = node.data.datatype.rstrip("[]")
        if datatype in type_map:
            target_type = type_map[datatype]
            ref["type"] = target_type[0]
            if len(target_type) > 1:
                ref["minimum"] = target_type[1]
            if len(target_type) > 2:
                ref["maximum"] = target_type[2]
            if node.data.min is not None:
                ref["minimum"] = node.data.min
            if node.data.max is not None:
                ref["maximum"] = node.data.max
            if node.data.allowed:
                ref["enum"] = node.data.allowed
        else:
            fqn = resolve_datatype(node.data.datatype, node.get_fqn()).rstrip("[]")
            type_node = find_type_node(dtree, fqn)
            if not type_node:
                raise JsonSchemaExporterException()
            add_node(ref, type_node, dtree, no_additional_props, require_all_properties, extend_all_attributes)
    else:
        schema["properties"] = {}
        if no_additional_props:
            schema["additionalProperties"] = False
        for child in node.children:
            if require_all_properties:
                if "required" in schema:
                    schema["required"].append(child.name)
                else:
                    schema["required"] = [child.name]
            schema["properties"][child.name] = {}
            add_node(
                schema["properties"][child.name],
                child,
                dtree,
                no_additional_props,
                require_all_properties,
                extend_all_attributes,
            )
