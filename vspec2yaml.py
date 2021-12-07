#!/usr/bin/env python3

#
# (c) 2016 Jaguar Land Rover
# (c) 2021 Robert Bosch GmbH
# (c) 2021 Pavel Sokolov (pavel.sokolov@gmail.com)
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert all vspec input files to a single flat YAML file.
#

import sys
import vspec
import yaml
import argparse
from vspec.model.vsstree import VSSNode, VSSType


def export_node(yaml_dict, node, generate_uuid):

    node_path = node.qualified_name()

    yaml_dict[node_path] = {}

    yaml_dict[node_path]["type"] = str(node.type.value)

    if node.type == VSSType.SENSOR or node.type == VSSType.ACTUATOR or node.type == VSSType.ATTRIBUTE:
        yaml_dict[node_path]["datatype"] = str(node.data_type.value)

    # many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        yaml_dict[node_path]["min"] = node.min
    if node.max != "":
        yaml_dict[node_path]["max"] = node.max
    if node.enum != "":
        yaml_dict[node_path]["enum"] = node.enum
    if node.default_value != "":
        yaml_dict[node_path]["default"] = node.default_value
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
    if generate_uuid:
        yaml_dict[node_path]["uuid"] = node.uuid

    for child in node.children:
        export_node(yaml_dict, child, generate_uuid)


def export_yaml(file, root, generate_uuids):
    yaml_dict = {}
    export_node(yaml_dict, root, generate_uuids)
    yaml.dump(yaml_dict, file, default_flow_style=False, Dumper=NoAliasDumper,
              sort_keys=False, width=1024, indent=2, encoding='utf-8', allow_unicode=True)


# create dumper to remove aliases from output and to add nice new line after each object for a better readability
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()


if __name__ == "__main__":
    # The arguments we accept

    parser = argparse.ArgumentParser(description='Convert vspec to yaml.')
    parser.add_argument('-I', '--include-dir', action='append',  metavar='dir', type=str,
                    help='Add include directory to search for included vspec files.')
    parser.add_argument('-s', '--strict', action='store_true', help='Use strict checking: Terminate when non-core attribute is found.' )
    parser.add_argument('--no-uuid', action='store_true', help='Exclude uuids from generated yaml.' )
    parser.add_argument('vspec_file', metavar='<vspec_file>', help='The vehicle specification file to convert.')
    parser.add_argument('yaml_file', metavar='<yaml file>', help='The file to output the YAML objects to.')

    args = parser.parse_args()

    strict = args.strict
    generate_uuids = not args.no_uuid

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    yaml_out = open(args.yaml_file, "w", encoding="utf-8")


    try:
        print("Loading vspec...")
        tree = vspec.load_tree(
            args.vspec_file, include_dirs, merge_private=False, break_on_noncore_attribute=strict)
        print("Recursing tree and creating YAML...")
        export_yaml(yaml_out, tree, generate_uuids)
        print("All done.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)
