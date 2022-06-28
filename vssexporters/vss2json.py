#!/usr/bin/env python3

# (c) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec tree to JSON

import argparse
import json
from vspec.model.vsstree import VSSNode, VSSType


def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('--json-all-extended-attributes', action='store_true',
                        help="Generate all extended attributes found in the model (default is generating only those given by the -e/--extended-attributes parameter).")
    parser.add_argument('--json-pretty', action='store_true',
                        help=" Pretty print JSON output.")


def export_node(json_dict, node, config):

    json_dict[node.name] = {}

    if node.type == VSSType.SENSOR or node.type == VSSType.ACTUATOR or node.type == VSSType.ATTRIBUTE:
        json_dict[node.name]["datatype"] = str(node.datatype.value)

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

    if not config.no_uuid:
        json_dict[node.name]["uuid"] = node.uuid

    for k, v in node.extended_attributes.items():
        if not config.json_all_extended_attributes and k not in VSSNode.whitelisted_extended_attributes:
            continue
        json_dict[node.name][k] = v

    # Might be better to not generate child dict, if there are no children
    # if node.type == VSSType.BRANCH and len(node.children) != 0:
    #    json_dict[node.name]["children"]={}

    # But old JSON code always generates children, so lets do so to
    if node.type == VSSType.BRANCH:
        json_dict[node.name]["children"] = {}

    for child in node.children:
        export_node(json_dict[node.name]["children"], child, config)


def export(config: argparse.Namespace, root: VSSNode):
    print("Generating JSON output...")
    json_dict = {}
    export_node(json_dict, root, config)
    outfile = open(config.output_file, 'w')
    if config.json_pretty:
        print("Serializing pretty JSON...")
        json.dump(json_dict, outfile, indent=2, sort_keys=True)
    else:
        print("Serializing compact JSON...")
        json.dump(json_dict, outfile, indent=None, sort_keys=True)
