#!/usr/bin/env python3

# Copyright (c) 2021 GENIVI Alliance
# Copyright (c) 2021 Motius GmbH
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Convert vspec file to graphql.  Derived from vspec2protobuf converter.
#
# NOTE: This uses
# input files where all instantiations have been done.  In other words,
# similar to the protobuf approach it is taking a simple approach and
# defines a new type for every instance, which is probably not required
# in a smarter schema.

import sys
import os
#Add path to main py vspec  parser
myDir= os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, ".."))

import vspec
import getopt
from anytree import PreOrderIter
from vspec.model.vsstree import VSSNode

# For the initial graphql examplewe had all types mapped to a non-specified size,
# e.g. "Int" so this is following that example.  I am not sure if this
# can/should be changed later.
mapped = {
    "uint64": "Int",
    "uint32": "Int",
    "uint16": "Int",
    "uint8": "Int",
    "int64": "Int",
    "int32": "Int",
    "int16": "Int",
    "int8": "Int",
    "float": "Float",
    "boolean": "Boolean",
    "string": "String"
}

# Currently we only have types that are indented one level so this is very
# crude.  For a more advanced generator, this might keep track of the
# current indentation level...
indent = '   '
def traverse_tree(tree, graphql_file):
    tree_node: VSSNode
    for tree_node in filter(lambda n: n.is_branch(), PreOrderIter(tree)):
        graphql_file.write(indent + '"""\n')
        graphql_file.write(indent + tree_node.description + "\n")
        graphql_file.write(indent + '"""\n')
        graphql_file.write(indent + f"type {tree_node.qualified_name('_')} {{" + "\n")
        print_message_body(tree_node.children, graphql_file)
        graphql_file.write(indent + "}\n\n")

def print_message_body(nodes, graphql_file):
    for i, node in enumerate(nodes, 1):
        data_type = node.qualified_name('_')
        if not node.is_branch():
            dt_val = node.data_type.value
            data_type = mapped.get(dt_val.strip("[]"), dt_val.strip("[]"))
            if data_type is None:
                print(f"WARNING: Could not map type {{dt_val}}!\n")
            if dt_val.endswith("[]"):  # Array type
                data_type = f"[{data_type}]"
        # Not sure if it matters but the example file we had, had
        # CamelCase but starting lower case
        name = node.name[0].lower() + node.name[1:]
        graphql_file.write(indent * 2 + '"""\n')
        graphql_file.write(indent * 2 + node.description + "\n")
        graphql_file.write(indent * 2 + '"""\n')
        graphql_file.write(indent * 2 + f"{name}: {data_type}\n\n")

def usage():
    print(
        """Usage: vspec2graphql.py [-I include_dir] ... [-i prefix:uuid_file] vspec_file output_file
  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple times.

  -i prefix:uuid_file  File to use for storing generated UUIDs for signals with
                       a given path prefix. Can be used multiple times to store
                       UUIDs for signal sub-trees in different files.

  vspec_file            The vehicle specification file to parse.
  output_file           The file to write graphql schema to.)
"""
    )
    sys.exit(255)


if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:i:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        elif o == "-i":
            id_spec = a.split(":")
            if len(id_spec) != 2:
                print("ERROR: -i needs a 'prefix:id_file' argument.")
                usage()

            [prefix, file_name] = id_spec
            vspec.db_mgr.create_signal_uuid_db(prefix, file_name)
        else:
            usage()

    if len(args) != 2:
        usage()

    graphql_file = open(args[1], "w")
    graphql_file.write("import { gql } from 'apollo-server';\n\n")
    graphql_file.write("const Vehicle = gql`\n")

    try:
        tree = vspec.load_tree(args[0], include_dirs)
        traverse_tree(tree, graphql_file)
    except vspec.VSpecError as e:
        print("Error: {}".format(e))
        exit(255)

    graphql_file.write("`;\n")
    graphql_file.write("export default Vehicle;\n")
    graphql_file.close()

