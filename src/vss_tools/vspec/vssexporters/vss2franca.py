# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to franca


from io import TextIOWrapper
from pathlib import Path

import rich_click as click
from anytree import PreOrderIter

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode


# Write the header line
def print_franca_header(file, version="unknown"):
    file.write(f"""
// Copyright (C) 2022, COVESA
//
// This program is licensed under the terms and conditions of the
// Mozilla Public License, version 2.0.  The full text of the
// Mozilla Public License is at https://www.mozilla.org/MPL/2.0/

const UTF8String VSS_VERSION = "{version}"

struct SignalSpec {{
    UInt32 id
    String name
    String type
    String description
    String datatype
    String unit
    Double min
    Double max
}}

const SignalSpec[] signal_spec = [
""")


# Write the data lines
def print_franca_content(file: TextIOWrapper, root: VSSNode, with_uuid: bool) -> None:
    output = ""
    node: VSSNode
    for node in PreOrderIter(root):
        data = node.get_vss_data()
        if node.parent:
            if output:
                output += ",\n{"
            else:
                output += "{"
            output += f'\tname: "{node.get_fqn()}"'
            output += f',\n\ttype: "{data.type.value}"'
            output += f',\n\tdescription: "{data.description}"'
            datatype = getattr(data, "datatype", None)
            if datatype:
                output += f',\n\tdatatype: "{datatype}"'
            if with_uuid:
                output += f',\n\tuuid: "{node.uuid}"'
            unit = getattr(data, "unit", None)
            if unit:
                output += f',\n\tunit: "{unit}"'
            min = getattr(data, "min", None)
            if min is not None:
                output += f",\n\tmin: {min}"
            max = getattr(data, "max", None)
            if max is not None:
                output += f",\n\tmax: {max}"
            allowed = getattr(data, "allowed", None)
            if allowed:
                output += f",\n\tallowed: {allowed}"
            output += "\n}"
    file.write(output)


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
@click.option("--franca-vss-version", help="Adds franca version info.")
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
    franca_vss_version: str,
):
    """
    Export as Franca.
    """
    log.info("Generating Franca output...")
    tree, datatype_tree = get_trees(
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
    with open(output, "w") as f:
        print_franca_header(f, franca_vss_version)
        print_franca_content(f, tree, uuid)
        f.write("\n]")
