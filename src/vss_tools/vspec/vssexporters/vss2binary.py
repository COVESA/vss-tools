# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to binary format
#
# This is the pure Python version of the binary exporter. The
# format has been taken from the C version at
# https://github.com/COVESA/vss-tools/blob/4.2/binary/binarytool.c
# This is a basic "length"/"data" format, where the length is in front
# of each field, and the field order is fixed.
#
# The length fields are mostly 8 bit (i.e. long strings/paths are not
# supported) with the exception of description and allowed (16 bit).
# The order of fields (where each field is composed of
# fieldlength + fielddata) is:
#
# name (vsspath), type, uuid, description, datatype, min, max, unit,
# allowed, default, validate
#
# if a field is not present (e.g. min, max, unit, allowed, default, validate),
# the length is 0.

import struct
from pathlib import Path
from typing import BinaryIO

import rich_click as click

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode


def allowedString(allowedList):
    allowedStr = ""
    for elem in allowedList:
        allowedStr += hexAllowedLen(elem) + elem
    return allowedStr


def hexAllowedLen(allowed):
    hexDigit1 = len(allowed) // 16
    hexDigit2 = len(allowed) - hexDigit1 * 16
    return "".join([intToHexChar(hexDigit1), intToHexChar(hexDigit2)])


def intToHexChar(hexInt):
    if hexInt < 10:
        return chr(hexInt + ord("0"))
    else:
        return chr(hexInt - 10 + ord("A"))


# Create a struct containing the length of the string as uint8
#  and the string itself
def create_l8v_string(s: str) -> bytes:
    pack = struct.pack(f"{len(s)+1}p", s.encode())
    # log.debug(f"create_l8v_string: {s} as {pack.hex()}")
    return pack


# Create a struct containing the length of the string as uint16
#  and the string itself
def create_l16v_string(s: str) -> bytes:
    pack = struct.pack(f"=H{len(s)}s", len(s), s.encode())
    # log.debug(f"create_l16v_string: {s} as {pack.hex()}")
    return pack


def export_node(node: VSSNode, generate_uuid, f: BinaryIO):
    data = node.get_vss_data().as_dict()

    f.write(create_l8v_string(node.name))
    f.write(create_l8v_string(data.get("type", "")))
    if node.uuid is None:
        log.debug(("No UUID for node %s", node.name))
        f.write(struct.pack("B", 0))
    else:
        f.write(create_l8v_string(node.uuid))

    f.write(create_l16v_string(data.get("description", "")))
    f.write(create_l8v_string(data.get("datatype", "")))
    f.write(create_l8v_string(str(data.get("min", ""))))
    f.write(create_l8v_string(str(data.get("max", ""))))
    f.write(create_l8v_string(data.get("unit", "")))

    if data.get("allowed") is None:
        f.write(struct.pack("H", 0))
    else:
        f.write(create_l16v_string(allowedString(data.get("allowed", ""))))

    f.write(create_l8v_string(str(data.get("default", ""))))
    f.write(create_l8v_string(str(data.get("validate", ""))))

    f.write(struct.pack("B", len(node.children)))

    for child in node.children:
        export_node(child, generate_uuid, f)


@click.command()
@clo.vspec_opt
@clo.output_required_opt
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
):
    """
    Export to Binary.
    """

    tree, _ = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        uuid=uuid,
        quantities=quantities,
        units=units,
        overlays=overlays,
    )
    log.info("Generating binary output...")
    with open(str(output), "wb") as f:
        export_node(tree, uuid, f)
    log.info("Binary output generated in %s", output)
