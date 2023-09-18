#!/usr/bin/env python3
#
# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
#
# Convert vspec tree to OpenAPI compatible JSON schema


from vspec.model.vsstree import VSSNode
import argparse
import json
import logging
from typing import Dict, Any
from vspec.loggingconfig import initLogging

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
    "string[]": "array"
}


def add_arguments(parser: argparse.ArgumentParser):
    parser.description = "The JSON schema exporter does not support any additional arguments."


def export_node(json_dict, node, config, print_uuid):
    # TODO adding json schema version might be great
    # TODO check if needed, formating of jsonschema is also possible
    # tags starting with $ sign are left for custom extensions and they are not part of official JSON Schema
    json_dict[node.name] = {
        "$VSStype": str(node.type.value),
        "description": node.description,
    }

    if node.is_signal() or node.is_property():
        json_dict[node.name]["$datatype"] = node.data_type_str
        json_dict[node.name]["type"] = type_map[node.data_type_str]

        # TODO map types, unless we want to keep original

    # many optional attributes are initialized to "" in vsstree.py
    if node.min != "":
        json_dict[node.name]["minimum"] = node.min
    if node.max != "":
        json_dict[node.name]["maximum"] = node.max
    if node.allowed != "":
        json_dict[node.name]["enum"] = node.allowed
    if node.default != "":
        json_dict[node.name]["default"] = node.default
    if node.deprecation != "":
        json_dict[node.name]["$deprecation"] = node.deprecation
    if node.is_struct():
        # change type to object
        json_dict[node.type]["type"] = "object"

    # in case of unit or aggregate, the attribute will be missing
    try:
        json_dict[node.name]["unit"] = str(node.unit.value)
    except AttributeError:
        pass
    try:
        json_dict[node.name]["$aggregate"] = node.aggregate
        if node.aggregate is True:
            # change type to object
            json_dict[node.type]["type"] = "object"
    except AttributeError:
        pass

    if node.comment != "":
        json_dict[node.name]["comment"] = node.comment

    if print_uuid:
        json_dict[node.name]["$uuid"] = node.uuid

    for k, v in node.extended_attributes.items():
        json_dict[node.name][k] = v

    # Generate child nodes
    if node.is_branch() or node.is_struct():
        # todo if struct, type could be linked to object and then list elements as properties
        json_dict[node.name]["$children"] = {}
        for child in node.children:
            export_node(json_dict[node.name]["$children"], child, config, print_uuid)


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid, data_type_root: VSSNode):
    logging.info("Generating JSON chema...")
    indent = None
    if config.json_pretty:
        logging.info("Serializing pretty JSON schema...")
        indent = 2

    signals_json_schema: Dict[str, Any] = {}
    export_node(signals_json_schema, signal_root, config, print_uuid)

    # Add data types to the schema
    if data_type_root is not None:
        data_types_json_schema: Dict[str, Any] = {}
        export_node(data_types_json_schema, data_type_root, config, print_uuid)
        signals_json_schema["$ComplexDataTypes"] = data_types_json_schema

    with open(config.output_file, 'w') as f:

        json.dump(signals_json_schema, f, indent=indent, sort_keys=True)


if __name__ == "__main__":
    initLogging()
