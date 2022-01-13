#!/usr/bin/env python3

#
# (c) 2016 Jaguar Land Rover
# (c) 2021 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec files to JSON
#

import sys
import vspec
import json
import argparse

from vspec.model.vsstree import VSSNode, VSSType


def export_node(json_dict, node, generate_uuid):

    json_dict[node.name] = {}

    if node.type == VSSType.SENSOR or node.type == VSSType.ACTUATOR or node.type == VSSType.ATTRIBUTE:
        json_dict[node.name]["datatype"] = str(node.data_type.value)

    json_dict[node.name]["type"] = str(node.type.value)

    # many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        json_dict[node.name]["min"] = node.min
    if node.max != "":
        json_dict[node.name]["max"] = node.max
    if node.allowed != "":
        json_dict[node.name]["allowed"] = node.allowed
    if node.default_value != "":
        json_dict[node.name]["default"] = node.default_value
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

    if generate_uuid:
        json_dict[node.name]["uuid"] = node.uuid

    # Might be better to not generate child dict, if there are no children
    # if node.type == VSSType.BRANCH and len(node.children) != 0:
    #    json_dict[node.name]["children"]={}

    # But old JSON code always generates children, so lets do so to
    if node.type == VSSType.BRANCH:
        json_dict[node.name]["children"] = {}

    for child in node.children:
        export_node(json_dict[node.name]["children"], child, generate_uuid)


def export_json(file, root, generate_uuids=True):
    json_dict = {}
    export_node(json_dict, root, generate_uuids)
    json.dump(json_dict, file, indent=2, sort_keys=True)


if __name__ == "__main__":
    # The arguments we accept

    parser = argparse.ArgumentParser(description='Convert vspec to json.')
    parser.add_argument('-I', '--include-dir', action='append',  metavar='dir', type=str,  default=[],
                    help='Add include directory to search for included vspec files.')
    parser.add_argument('-s', '--strict', action='store_true', help='Use strict checking: Terminate when anything not covered or not recommended by the core VSS specs is found.')
    parser.add_argument('--abort-on-non-core-attribute', action='store_true', help=" Terminate when non-core attribute is found.")
    parser.add_argument('--abort-on-name-style', action='store_true', help=" Terminate naming style not follows recommendations.")
    parser.add_argument('--no-uuid', action='store_true', help='Exclude uuids from generated json.' )
    parser.add_argument('vspec_file', metavar='<vspec_file>', help='The vehicle specification file to convert.')
    parser.add_argument('json_file', metavar='<json file>', help='The file to output the JSON objects to.')

    args = parser.parse_args()

    generate_uuids=not args.no_uuid

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    json_out = open(args.json_file, "w")

    abort_on_non_core_attribute = False
    abort_on_namestyle = False

    if args.abort_on_non_core_attribute  or args.strict:
        abort_on_non_core_attribute = True
    if args.abort_on_name_style or args.strict:
        abort_on_namestyle = True


    try:
        print("Loading vspec...")
        tree = vspec.load_tree(
            args.vspec_file, include_dirs, merge_private=False, break_on_noncore_attribute=abort_on_non_core_attribute, break_on_name_style_violation=abort_on_namestyle)
        print("Recursing tree and creating JSON...")
        export_json(json_out, tree, generate_uuids)
        print("All done.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        sys.exit(255)
