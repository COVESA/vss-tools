#!/usr/bin/env python3

# (c) 2022 Geotab Inc
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec tree to binary format

import argparse
import logging
import ctypes
import os.path
from vspec.model.vsstree import VSSNode, VSSType

out_file = ""
_cbinary = None


def createBinaryCnode(fname, nodename, nodetype, uuid, description, nodedatatype, nodemin, nodemax, unit, allowed,
                      defaultAllowed, validate, children):
    global _cbinary
    _cbinary.createBinaryCnode(fname, nodename, nodetype, uuid, description, nodedatatype, nodemin, nodemax, unit,
                               allowed, defaultAllowed, validate, children)


def allowedString(allowedList):
    allowedStr = ""
    for elem in allowedList:
        allowedStr += hexAllowedLen(elem) + elem
#    print("allowedstr=" + allowedStr + "\n")
    return allowedStr


def hexAllowedLen(allowed):
    hexDigit1 = len(allowed) // 16
    hexDigit2 = len(allowed) - hexDigit1*16
#    print("Hexdigs:" + str(hexDigit1) + str(hexDigit2))
    return "".join([intToHexChar(hexDigit1), intToHexChar(hexDigit2)])


def intToHexChar(hexInt):
    if (hexInt < 10):
        return chr(hexInt + ord('0'))
    else:
        return chr(hexInt - 10 + ord('A'))


def add_arguments(parser: argparse.ArgumentParser):
    parser.description = "The binary exporter does not support any additional arguments."


def export_node(node, generate_uuid, out_file):
    nodename = str(node.name)
    b_nodename = nodename.encode('utf-8')

    nodetype = str(node.type.value)
    b_nodetype = nodetype.encode('utf-8')

    nodedescription = str(node.description)
    b_nodedescription = nodedescription.encode('utf-8')

    children = len(node.children)

    nodedatatype = ""
    nodemin = ""
    nodemax = ""
    nodeunit = ""
    nodeallowed = ""
    nodedefault = ""
    nodeuuid = ""
    nodevalidate = ""  # exported to binary

    if node.type == VSSType.SENSOR or node.type == VSSType.ACTUATOR or node.type == VSSType.ATTRIBUTE:
        nodedatatype = str(node.datatype.value)
    b_nodedatatype = nodedatatype.encode('utf-8')

    # many optional attributes are initilized to "" in vsstree.py
    if node.min != "":
        nodemin = str(node.min)
    b_nodemin = nodemin.encode('utf-8')

    if node.max != "":
        nodemax = str(node.max)
    b_nodemax = nodemax.encode('utf-8')

    if node.allowed != "":
        nodeallowed = allowedString(node.allowed)
    b_nodeallowed = nodeallowed.encode('utf-8')

    if node.default != "":
        nodedefault = str(node.default)
    b_nodedefault = nodedefault.encode('utf-8')

    # in case of unit or aggregate, the attribute will be missing
    try:
        nodeunit = str(node.unit.value)
    except AttributeError:
        pass
    b_nodeunit = nodeunit.encode('utf-8')

    if generate_uuid:
        nodeuuid = node.uuid
    b_nodeuuid = nodeuuid.encode('utf-8')

    if "validate" in node.extended_attributes:
        nodevalidate = node.extended_attributes["validate"]
    b_nodevalidate = nodevalidate.encode('utf-8')

    b_fname = out_file.encode('utf-8')

    createBinaryCnode(b_fname, b_nodename, b_nodetype, b_nodeuuid, b_nodedescription, b_nodedatatype, b_nodemin,
                      b_nodemax, b_nodeunit, b_nodeallowed, b_nodedefault, b_nodevalidate, children)

    for child in node.children:
        export_node(child, generate_uuid, out_file)


def export(config: argparse.Namespace, root: VSSNode, print_uuid):
    global _cbinary
    dllName = "../../binary/binarytool.so"
    dllAbsPath = os.path.dirname(os.path.abspath(__file__)) + os.path.sep + dllName
    if not os.path.isfile(dllAbsPath):
        logging.error("The required library binarytool.so is not available, exiting!")
        logging.info("You must build the library, "
                     "see https://github.com/COVESA/vss-tools/blob/master/binary/README.md!")
        return
    _cbinary = ctypes.CDLL(dllAbsPath)

    _cbinary.createBinaryCnode.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                           ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                           ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                           ctypes.c_int)

    logging.info("Generating binary output...")
    out_file = config.output_file
    export_node(root, print_uuid, out_file)
    logging.info("Binary output generated in " + out_file)
