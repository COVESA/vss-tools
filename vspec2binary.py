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
# Convert vspec file to a platform binary format.
#

import sys
import os
import vspec
import json
import getopt
import ctypes

def usage():
    print(("Usage:", sys.argv[0], "[-I include_dir] ... [-i prefix:id_file] vspec_file franca_file"))
    print ("  -I include_dir       Add include directory to search for included vspec")
    print ("                       files. Can be used multiple timees.")
    print ("\n")
    print ("  -i prefix:uuid_file  File to use for storing generated UUIDs for signals with")
    print ("                       a given path prefix. Can be used multiple times to store")
    print ("                       UUIDs for signal sub-trees in different files.")
    print ("\n")
    print (" vspec_file            The vehicle specification file to parse.")
    print (" franca_file           The file to output the Franca IDL spec to.")
    sys.exit(255)

import os.path
dllName = "binary/binarytool.so"
dllAbsPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + dllName
_cbinary = ctypes.CDLL(dllAbsPath)

#void createBinaryCnode(char* fname, char* name, char* type, char* uuid, char* descr, char* datatype, char* min, char* max, char* unit, char* enums, char* defaultEnum, char* validate, int children);
_cbinary.createBinaryCnode.argtypes = (ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int)

def createBinaryCnode(fname, nodename, nodetype, uuid, description, nodedatatype, nodemin, nodemax, unit, enums, defaultEnum, validate, children):
    global _cbinary
    _cbinary.createBinaryCnode(fname, nodename, nodetype, uuid, description, nodedatatype, nodemin, nodemax, unit, enums, defaultEnum, validate, children)

def enumString(enumList):
    enumStr = ""
    for elem in enumList:
        enumStr += hexEnumLen(elem) + elem
#    print("enumstr=" + enumStr + "\n")
    return enumStr

def hexEnumLen(enum):
    hexDigit1 = len(enum) // 16
    hexDigit2 = len(enum) - hexDigit1*16
#    print("Hexdigs:" + str(hexDigit1) + str(hexDigit2))
    return "".join([intToHexChar(hexDigit1), intToHexChar(hexDigit2)])

def intToHexChar(hexInt):
    if (hexInt < 10):
        return chr(hexInt + ord('0'))
    else:
        return chr(hexInt - 10 + ord('A'))

def create_node_legacy(key, val, b_nodename, b_nodetype, b_nodeuuid, b_nodedescription, children):
    nodedatatype = ""
    nodemin = ""
    nodemax = ""
    nodeunit = ""
    nodeenum = ""
    nodedefault = ""
    nodevalidate = ""

    if "datatype" in val:
        nodedatatype = val["datatype"]

    if "min" in val:
        nodemin = str(val["min"])

    if "max" in val:
        nodemax = str(val["max"])

    if "unit" in val:
        nodeunit = val["unit"]

    if "enum" in val:
        nodeenum = enumString(val["enum"])

    if "default" in val:
        nodedefault = str(val["default"])

    if "validate" in val:
        nodevalidate = val["validate"]

    b_nodedatatype = nodedatatype.encode('utf-8')
    b_nodemin = nodemin.encode('utf-8')
    b_nodemax = nodemax.encode('utf-8')
    b_nodeunit = nodeunit.encode('utf-8')
    b_nodeenum = nodeenum.encode('utf-8')
    b_nodedefault = nodedefault.encode('utf-8')
    b_nodevalidate = nodevalidate.encode('utf-8')

    b_fname = args[1].encode('utf-8')

    createBinaryCnode(b_fname, b_nodename, b_nodetype, b_nodeuuid, b_nodedescription, b_nodedatatype, b_nodemin, b_nodemax, b_nodeunit, b_nodeenum, b_nodedefault, b_nodevalidate, children)

def create_node(key, val):
    nodename = key
    b_nodename = nodename.encode('utf-8')
    nodetype = val['type']
    b_nodetype = nodetype.encode('utf-8')
    nodeuuid = val['uuid']
    b_nodeuuid = nodeuuid.encode('utf-8')
    nodedescription = val['description']
    b_nodedescription = nodedescription.encode('utf-8')
    children = 0
    if "children" in val:
        children = len(list(val["children"].keys()))

    create_node_legacy(key, val, b_nodename, b_nodetype, b_nodeuuid, b_nodedescription, children)


def traverse_tree(tree):
    # Traverse all elemnts in tree.
    for key, val in tree.items():
        # Is this a branch?
        if "children" in val:
            # Yes. Recurse
            create_node(key, val)
            traverse_tree(val['children'])
            continue
        create_node(key, val)


if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args= getopt.getopt(sys.argv[1:], "I:i:v:")

    # Always search current directory for include_file
    vss_version = "unspecified version"
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        elif o == "-v":
            vss_version = a
        elif o == "-i":
            id_spec = a.split(":")
            if len(id_spec) != 2:
                print ("ERROR: -i needs a 'prefix:id_file' argument.")
                usage()

            [prefix, file_name] = id_spec
            vspec.db_mgr.create_signal_uuid_db(prefix, file_name)
        else:
            usage()

    if len(args) != 2:
        usage()

    try:
        tree = vspec.load(args[0], include_dirs)
    except vspec.VSpecError as e:
        print(("Error: {}".format(e)))
        exit(255)

    traverse_tree(tree)
