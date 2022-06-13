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

mapped = {
    "uint16": "uint32",
    "uint8": "uint32",
    "int8": "int32",
    "int16": "int32",
    "boolean": "bool",
}


def traverse_tree(tree, proto_file):
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


def usage():
    print(
        """Usage: vspec2protobuf.py [-I include_dir] ... vspec_file output_file
  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple times.
 vspec_file            The vehicle specification file to parse.
 proto_file            The file to output the proto file to.)
       """
    )
    sys.exit(255)


if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        else:
            usage()

    if len(args) != 2:
        usage()

    proto_file = open(args[1], "w")
    proto_file.write('syntax = "proto3";\n\n')
    proto_file.write("package vehicle;\n\n")

    try:
        tree = vspec.load_tree(args[0], include_dirs)
        traverse_tree(tree, proto_file)
    except vspec.VSpecError as e:
        print("Error: {}".format(e))
        exit(255)

    proto_file.close()
