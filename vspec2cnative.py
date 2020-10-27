#!/usr/bin/env python3

#
# (C) 2020 Geotab Inc
# (C) 2018 Volvo Cars
# (C) 2016 Jaguar Land Rover
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec file to a platform C native format.
#

import sys
import os
import vspec
import json
import getopt
import ctypes

from anytree import RenderTree, PreOrderIter
from model.vsstree import VSSNode


def usage():
    print(f"""
Usage: {sys.argv[0]} [options] vspec_file cnative_file

  where [options] are:

  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple timees.

  -i prefix:uuid_file  "prefix" is an optional string that will be
                       prepended to each signal name defined in the
                       vspec file.

                       "uuid_file" is the name of the file containing the
                       static UUID values for the signals.  This file is
                       read/write and will be updated if necessary.

                       This option can be specified several times in
                       to store the UUIDs of different parts of the
                       signal tree in different files.

  vspec_file           The vehicle specification file to parse.

  cnative_file         The file to output the cnative data to.
""")
    sys.exit(255)

import os.path
dllName = "c_native/cnativenodelib.so"
dllAbsPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + dllName
_cnative = ctypes.CDLL(dllAbsPath)

#void createNativeCnode(char* fname, char* name, char* type, char* uuid, int validate, char* descr, int children, char* datatype, char* min, char* max, char* unit, char* enums);
_cnative.createNativeCnode.argtypes = (ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p)

def createNativeCnode(fname, nodename, nodetype, uuid, validate, description, children, nodedatatype, nodemin, nodemax, unit, enums):
    global _cnative
    _cnative.createNativeCnode(fname, nodename, nodetype, uuid, validate, description, children, nodedatatype, nodemin, nodemax, unit, enums)


def enumString(enumList):
    enumStr = "/"
    for elem in enumList:
        enumStr += elem + "/"
    return enumStr

def create_node_legacy(tree_node, b_nodename, b_nodetype, b_nodeuuid, validate, b_nodedescription, children):

    nodedatatype = tree_node.data_type.value if tree_node.has_data_type() else ""
    nodeunit = tree_node.unit.value if tree_node.has_unit() else ""
    nodemin = str(tree_node.min)
    nodemax = str(tree_node.max)
    nodeenum = enumString(tree_node.enum)

    b_nodedatatype = nodedatatype.encode('utf-8')
    b_nodemin = nodemin.encode('utf-8')
    b_nodemax = nodemax.encode('utf-8')
    b_nodeunit = nodeunit.encode('utf-8')
    b_nodeenum = nodeenum.encode('utf-8')

    b_fname = args[1].encode('utf-8')

    createNativeCnode(b_fname, b_nodename, b_nodetype, b_nodeuuid, validate, b_nodedescription, children, b_nodedatatype, b_nodemin, b_nodemax, b_nodeunit, b_nodeenum)


def create_node(tree_node):
    nodename = tree_node.name
    b_nodename = nodename.encode('utf-8')
    nodetype = tree_node.type.value
    b_nodetype = nodetype.encode('utf-8')
    nodeuuid = tree_node.uuid
    b_nodeuuid = nodeuuid.encode('utf-8')
    nodedescription = tree_node.description
    b_nodedescription = nodedescription.encode('utf-8')
    validate = 0
#    if "validate" in val:
#        nodevalidate = val["validate"]
#        if (nodevalidate == "write-only"):
#                validate = 1
#        elif (nodevalidate == "read-write"):
#                validate = 2
    children = len(tree_node.children)
#    if "children" in val:
#        children = len(list(val["children"].keys()))

    create_node_legacy(tree_node, b_nodename, b_nodetype, b_nodeuuid, validate, b_nodedescription, children)


def traverse_tree(tree):
    # Traverse all elements in tree.
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        create_node(tree_node)


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

    try:
        tree = vspec.load_tree(args[0], include_dirs)
        traverse_tree(tree)
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)


