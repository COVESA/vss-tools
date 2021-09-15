#!/usr/bin/env python3

# Copyright (c) 2021 GENIVI Alliance
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Generate code that can convert VSS signals to Android Automotive
# vehicle properties.
#

import sys
import os
import getopt
from anytree import PreOrderIter
import type_hal_parser
import read_mapping_layer

myDir= os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, "../.."))
import vspec
from vspec.model.vsstree import VSSNode, VSSType

def generate_from_tree(vss_tree, map_tree, type_table, output_file):
    print("GENERATING...")

def usage():
    print(
        """Usage: vspec2aaprop.py [-I include_dir] vspec_file mapping_file types_hal_file output_file
  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple times.
  vspec_file           The top-level vehicle specification file to parse.
  mapping_file         The VSS-layer that defines mapping between VSS and AA properties
  types_hal_file       The Android types.hal header file for VHAL type information.
  output_file          The primary file name to write C++ generated code to.)
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
        else:
            usage()

    if len(args) != 4:
        usage()

    try:
        tree = vspec.load_tree(args[0], include_dirs)
    except vspec.VSpecError as e:
        print("Error: {}".format(e))
        exit(255)

    map_tree = read_mapping_layer.load_tree(args[1])
    type_table = type_hal_parser.get_vehicleproperty(args[2])

    output_file = open(args[3], "w")
    generate_from_tree(tree, map_tree, type_table, output_file)

    output_file.write("//DONE\n")
    output_file.close()
