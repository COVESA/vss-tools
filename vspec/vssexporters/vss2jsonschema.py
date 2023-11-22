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
# Convert vspec tree compatible JSON schema

import argparse
import json
import logging
from typing import Dict, Any
from typing import Optional
from vspec.model.vsstree import VSSNode
from vspec.vss2x import Vss2X
from vspec.vspec2vss_config import Vspec2VssConfig

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


def export_node(json_dict, node, config, print_uuid):
    """Preparing nodes for JSON schema output."""
    # keyword with X- sign are left for extensions and they are not part of official JSON schema
    json_dict[node.name] = {
        "description": node.description,
    }

    if node.is_signal() or node.is_property():
        json_dict[node.name]["type"] = type_map[node.data_type_str]

    # many optional attributes are initialized to "" in vsstree.py
    if node.min != "":
        json_dict[node.name]["minimum"] = node.min
    if node.max != "":
        json_dict[node.name]["maximum"] = node.max
    if node.allowed != "":
        json_dict[node.name]["enum"] = node.allowed
    if node.default != "":
        json_dict[node.name]["default"] = node.default
    if node.is_struct():
        # change type to object
        json_dict[node.type]["type"] = "object"

    if config.jsonschema_all_extended_attributes:
        if node.type != "":
            json_dict[node.name]["x-VSStype"] = str(node.type.value)
        if node.data_type_str != "":
            json_dict[node.name]["x-datatype"] = node.data_type_str
        if node.deprecation != "":
            json_dict[node.name]["x-deprecation"] = node.deprecation

        # in case of unit or aggregate, the attribute will be missing
        try:
            json_dict[node.name]["x-unit"] = str(node.unit.value)
        except AttributeError:
            pass
        try:
            json_dict[node.name]["x-aggregate"] = node.aggregate
            if node.aggregate:
                # change type to object
                json_dict[node.type]["type"] = "object"
        except AttributeError:
            pass

        if node.comment != "":
            json_dict[node.name]["x-comment"] = node.comment

        if print_uuid:
            json_dict[node.name]["x-uuid"] = node.uuid

    for k, v in node.extended_attributes.items():
        json_dict[node.name][k] = v

    # Generate child nodes
    if node.is_branch() or node.is_struct():
        if config.jsonschema_disallow_additional_properties:
            json_dict[node.name]["additionalProperties"] = False
        json_dict[node.name]["properties"] = {}
        if config.jsonschema_require_all_properties:
            json_dict[node.name]["required"] = [child.name for child in node.children]
        for child in node.children:
            export_node(json_dict[node.name]["properties"], child, config, print_uuid)


class Vss2JsonSchema(Vss2X):

    def add_arguments(self, parser: argparse.ArgumentParser):
        """Check for input arguments."""
        parser.add_argument('--jsonschema-all-extended-attributes', action='store_true',
                            help="Generate all extended attributes found in the model."
                            "Should not be used with strict mode JSON Schema validators.")
        parser.add_argument("--jsonschema-disallow-additional-properties", action='store_true',
                            help="Do not allow properties not defined in VSS tree")
        parser.add_argument("--jsonschema-require-all-properties", action='store_true',
                            help="Require all elements defined in VSS tree for a valid object")
        parser.add_argument('--jsonschema-pretty', action='store_true',
                            help=" Pretty print JSON Schema output.")

    def generate(self, config: argparse.Namespace, signal_root: VSSNode, vspec2vss_config: Vspec2VssConfig,
                 data_type_root: Optional[VSSNode] = None) -> None:
        """Export function for generating JSON schema file."""
        logging.info("Generating JSON schema...")
        indent = None
        if config.jsonschema_pretty:
            logging.info("Serializing pretty JSON schema...")
            indent = 2

        signals_json_schema: Dict[str, Any] = {}
        export_node(signals_json_schema, signal_root, config, vspec2vss_config.generate_uuid)

        # Add data types to the schema
        if data_type_root is not None:
            data_types_json_schema: Dict[str, Any] = {}
            export_node(data_types_json_schema, data_type_root, config, vspec2vss_config.generate_uuid)
            if config.jsonschema_all_extended_attributes:
                signals_json_schema["x-ComplexDataTypes"] = data_types_json_schema

        # VSS models only have one root, so there should only be one
        # key in the dict
        assert (len(signals_json_schema.keys()) == 1)
        top_node_name = list(signals_json_schema.keys())[0]
        signals_json_schema = signals_json_schema.pop(top_node_name)

        json_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": top_node_name,
            "type": "object",
            **signals_json_schema}
        with open(config.output_file, 'w', encoding="utf-8") as output_file:
            json.dump(json_schema, output_file, indent=indent, sort_keys=False)
