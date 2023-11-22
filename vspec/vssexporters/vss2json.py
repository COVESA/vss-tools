#!/usr/bin/env python3

# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to JSON

from vspec.model.vsstree import VSSNode
import argparse
import json
import logging
from typing import Dict, Any
from typing import Optional
from vspec.vss2x import Vss2X
from vspec.vspec2vss_config import Vspec2VssConfig


def export_node(json_dict, node, config, print_uuid):

    json_dict[node.name] = {}

    if node.is_signal() or node.is_property():
        json_dict[node.name]["datatype"] = node.data_type_str

    json_dict[node.name]["type"] = str(node.type.value)

    # many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        json_dict[node.name]["min"] = node.min
    if node.max != "":
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
        if not config.json_all_extended_attributes and k not in VSSNode.whitelisted_extended_attributes:
            continue
        json_dict[node.name][k] = v

    # Include instance information if we run tool in "no-expand" mode
    if config.no_expand and node.instances is not None:
        json_dict[node.name]["instances"] = node.instances

    # Might be better to not generate child dict, if there are no children
    # if node.type == VSSType.BRANCH and len(node.children) != 0:
    #    json_dict[node.name]["children"]={}

    # But old JSON code always generates children, so lets do so to
    if node.is_branch() or node.is_struct():
        json_dict[node.name]["children"] = {}

    for child in node.children:
        export_node(json_dict[node.name]["children"],
                    child, config, print_uuid)


class Vss2Json(Vss2X):

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--json-all-extended-attributes', action='store_true',
                            help="Generate all extended attributes found in the model "
                                 "(default is generating only those given by the -e/--extended-attributes parameter).")
        parser.add_argument('--json-pretty', action='store_true',
                            help=" Pretty print JSON output.")

    def generate(self, config: argparse.Namespace, signal_root: VSSNode, vspec2vss_config: Vspec2VssConfig,
                 data_type_root: Optional[VSSNode] = None) -> None:
        logging.info("Generating JSON output...")
        indent = None
        if config.json_pretty:
            logging.info("Serializing pretty JSON...")
            indent = 2
        else:
            logging.info("Serializing compact JSON...")

        signals_json_dict: Dict[str, Any] = {}
        export_node(signals_json_dict, signal_root, config, vspec2vss_config.generate_uuid)

        if data_type_root is not None:
            data_types_json_dict: Dict[str, Any] = {}
            export_node(data_types_json_dict, data_type_root, config, vspec2vss_config.generate_uuid)
            if config.types_output_file is None:
                logging.info("Adding custom data types to signal dictionary")
                signals_json_dict["ComplexDataTypes"] = data_types_json_dict
            else:
                with open(config.types_output_file, 'w') as f:
                    json.dump(data_types_json_dict, f, indent=indent, sort_keys=True)

        with open(config.output_file, 'w') as f:
            json.dump(signals_json_dict, f, indent=indent, sort_keys=True)
