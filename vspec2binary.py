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
import argparse
import ctypes
import os.path

dllName = "binary/binarytool.so"
dllAbsPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + dllName
_cbinary = ctypes.CDLL(dllAbsPath)


out_file="undefined"

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

    b_fname = out_file.encode('utf-8')

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
    # The arguments we accept

    parser = argparse.ArgumentParser(description='Convert vspec to binary.')
    parser.add_argument('-I', '--include-dir', action='append',  metavar='dir', type=str, default=[],
                    help='Add include directory to search for included vspec files.')
    #parser.add_argument('-s', '--strict', action='store_true', help='Use strict checking: Terminate when non-core attribute is found.' )
    parser.add_argument('vspec_file', metavar='<vspec_file>', help='The vehicle specification file to convert.')
    parser.add_argument('bin_file', metavar='<bin file>', help='The file to output the binary representation to.')

    args = parser.parse_args()

    #strict=args.strict
    
    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    out_file=args.bin_file

    try:
        #This will break traverse_tree
        #tree = vspec.load_tree(
        #    args.vspec_file, include_dirs,  break_on_noncore_attribute=strict)
        #Using deprecated parser instead
        tree = vspec.load(args.vspec_file, include_dirs)


    except vspec.VSpecError as e:
        print(("Error: {}".format(e)))
        sys.exit(255)

    traverse_tree(tree)
