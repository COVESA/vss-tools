#!/usr/bin/env python3

# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to binary format

import ctypes
import os.path
from pathlib import Path
from vss_tools import log
import vss_tools.vspec.cli_options as clo
import rich_click as click
from vss_tools.vspec.model.vsstree import VSSType
from vss_tools.vspec.vssexporters.utils import get_trees

out_file = ""
_cbinary = None


def createBinaryCnode(
    fname,
    nodename,
    nodetype,
    uuid,
    description,
    nodedatatype,
    nodemin,
    nodemax,
    unit,
    allowed,
    defaultAllowed,
    validate,
    children,
):
    global _cbinary
    _cbinary.createBinaryCnode(
        fname,
        nodename,
        nodetype,
        uuid,
        description,
        nodedatatype,
        nodemin,
        nodemax,
        unit,
        allowed,
        defaultAllowed,
        validate,
        children,
    )


def allowedString(allowedList):
    allowedStr = ""
    for elem in allowedList:
        allowedStr += hexAllowedLen(elem) + elem
    #    print("allowedstr=" + allowedStr + "\n")
    return allowedStr


def hexAllowedLen(allowed):
    hexDigit1 = len(allowed) // 16
    hexDigit2 = len(allowed) - hexDigit1 * 16
    #    print("Hexdigs:" + str(hexDigit1) + str(hexDigit2))
    return "".join([intToHexChar(hexDigit1), intToHexChar(hexDigit2)])


def intToHexChar(hexInt):
    if hexInt < 10:
        return chr(hexInt + ord("0"))
    else:
        return chr(hexInt - 10 + ord("A"))


def export_node(node, generate_uuid, out_file):
    nodename = str(node.name)
    b_nodename = nodename.encode("utf-8")

    nodetype = str(node.type.value)
    b_nodetype = nodetype.encode("utf-8")

    nodedescription = str(node.description)
    b_nodedescription = nodedescription.encode("utf-8")

    children = len(node.children)

    nodedatatype = ""
    nodemin = ""
    nodemax = ""
    nodeunit = ""
    nodeallowed = ""
    nodedefault = ""
    nodeuuid = ""
    nodevalidate = ""  # exported to binary

    if (
        node.type == VSSType.SENSOR
        or node.type == VSSType.ACTUATOR
        or node.type == VSSType.ATTRIBUTE
    ):
        nodedatatype = str(node.datatype.value)
    b_nodedatatype = nodedatatype.encode("utf-8")

    # many optional attributes are initilized to "" in vsstree.py
    if node.min is not None:
        nodemin = str(node.min)
    b_nodemin = nodemin.encode("utf-8")

    if node.max is not None:
        nodemax = str(node.max)
    b_nodemax = nodemax.encode("utf-8")

    if node.allowed != "":
        nodeallowed = allowedString(node.allowed)
    b_nodeallowed = nodeallowed.encode("utf-8")

    if node.default != "":
        nodedefault = str(node.default)
    b_nodedefault = nodedefault.encode("utf-8")

    # in case of unit or aggregate, the attribute will be missing
    try:
        nodeunit = str(node.unit.value)
    except AttributeError:
        pass
    b_nodeunit = nodeunit.encode("utf-8")

    if generate_uuid:
        nodeuuid = node.uuid
    b_nodeuuid = nodeuuid.encode("utf-8")

    if "validate" in node.extended_attributes:
        nodevalidate = node.extended_attributes["validate"]
    b_nodevalidate = nodevalidate.encode("utf-8")

    b_fname = out_file.encode("utf-8")

    createBinaryCnode(
        b_fname,
        b_nodename,
        b_nodetype,
        b_nodeuuid,
        b_nodedescription,
        b_nodedatatype,
        b_nodemin,
        b_nodemax,
        b_nodeunit,
        b_nodeallowed,
        b_nodedefault,
        b_nodevalidate,
        children,
    )

    for child in node.children:
        export_node(child, generate_uuid, out_file)


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@click.option(
    "--bintool-dll",
    "-b",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    bintool_dll: Path,
):
    """
    Export to Binary.
    """
    global _cbinary
    _cbinary = ctypes.CDLL(str(bintool_dll))

    _cbinary.createBinaryCnode.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
    )

    tree, _ = get_trees(
        include_dirs,
        aborts,
        strict,
        extended_attributes,
        uuid,
        quantities,
        vspec,
        units,
        tuple(),
        None,
        overlays,
        True,
    )
    log.info("Generating binary output...")
    export_node(tree, uuid, str(output))
    log.info(f"Binary output generated in {output}")
