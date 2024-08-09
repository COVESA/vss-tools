# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to binary format

import ctypes
from pathlib import Path
from vss_tools import log
import vss_tools.vspec.cli_options as clo
import rich_click as click
from vss_tools.vspec.tree import VSSNode
from vss_tools.vspec.main import get_trees


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


def export_node(cdll: ctypes.CDLL, node: VSSNode, generate_uuid, out_file: str):
    uuid = "" if node.uuid is None else node.uuid
    data = node.get_vss_data().as_dict()
    cdll.createBinaryCnode(
        out_file.encode(),
        node.name.encode(),
        data.get("type", "").encode(),
        uuid.encode(),
        data.get("description", "").encode(),
        data.get("datatype", "").encode(),
        str(data.get("min", "")).encode(),
        str(data.get("max", "")).encode(),
        data.get("unit", "").encode(),
        b""
        if data.get("allowed") is None
        else allowedString(data.get("allowed", "")).encode(),
        str(data.get("default", "")).encode(),
        str(data.get("validate", "")).encode(),
        len(node.children),
    )
    for child in node.children:
        export_node(cdll, child, generate_uuid, out_file)


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
    cdll = ctypes.CDLL(str(bintool_dll))
    cdll.createBinaryCnode.argtypes = (
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
    export_node(cdll, tree, uuid, str(output))
    log.info(f"Binary output generated in {output}")
