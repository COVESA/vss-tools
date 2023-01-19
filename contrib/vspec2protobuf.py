#!/usr/bin/env python3

# Copyright (c) 2021 Motius GmbH
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Convert vspec file to proto
#

import sys
import os
#Add path to main py vspec  parser
myDir= os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, ".."))

import vspec
import getopt
from anytree import RenderTree, PreOrderIter
from vspec.model.vsstree import VSSNode
import argparse
from vspec.model.constants import Unit

mapped = {
    "uint16": "uint32",
    "uint8": "uint32",
    "int8": "int32",
    "int16": "int32",
    "boolean": "bool",
}


def traverse_tree(tree : VSSNode, proto_file):
    tree_node: VSSNode
    for tree_node in filter(lambda n: n.is_branch(), PreOrderIter(tree)):
        proto_file.write(f"message {tree_node.qualified_name('')} {{" + "\n")
        print_message_body(tree_node.children, proto_file)
        proto_file.write("}\n\n")


def print_message_body(nodes, proto_file):
    for i, node in enumerate(nodes, 1):
        data_type = node.qualified_name("")
        if not node.is_branch():
            dt_val = node.datatype.value
            data_type = mapped.get(dt_val.strip("[]"), dt_val.strip("[]"))
            data_type = ("repeated " if dt_val.endswith("[]") else "") + data_type
        proto_file.write(f"  {data_type} {node.name} = {i};" + "\n")



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert vspec to protobuf.")
    arguments = sys.argv[1:]

    parser.add_argument('-I', '--include-dir', action='append',  metavar='dir', type=str,  default=[],
                        help='Add include directory to search for included vspec files.')
    parser.add_argument('-u', '--unit-file', action='append',  metavar='unit_file', type=str,  default=[],
                        help='Unit file to be used for generation. Argument -u may be used multiple times.')
    parser.add_argument('vspec_file', metavar='<vspec_file>',
                        help='The vehicle specification file to convert.')
    parser.add_argument('output_file', metavar='<output_file>',
                        help='The file to write output to.')

    args = parser.parse_args(arguments)

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    if not args.unit_file:
        print("WARNING: Use of default VSS unit file is deprecated, please specify the unit file you want to use with the -u argument!")
        Unit.load_default_config_file()
    else:
        for unit_file in args.unit_file:
           print("Reading unit definitions from "+str(unit_file))
           Unit.load_config_file(unit_file)

    proto_file = open(args.output_file, "w")
    proto_file.write('syntax = "proto3";\n\n')
    proto_file.write("package vehicle;\n\n")

    try:
        tree = vspec.load_tree(args.vspec_file, include_dirs)
        traverse_tree(tree, proto_file)
    except vspec.VSpecError as e:
        print("Error: {}".format(e))
        exit(255)

    proto_file.close()
