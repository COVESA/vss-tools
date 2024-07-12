#!/usr/bin/env python3

# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to franca


import rich_click as click
from pathlib import Path
from vss_tools.vspec.vssexporters.utils import get_trees
import vss_tools.vspec.cli_options as clo
from anytree import PreOrderIter  # type: ignore[import]

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
def print_franca_content(file, tree, uuid):
    output = ""
    for tree_node in PreOrderIter(tree):
        if tree_node.parent:
            if output:
                output += ",\n{"
            else:
                output += "{"
            output += f"\tname: \"{tree_node.qualified_name('.')}\""
            output += f',\n\ttype: "{tree_node.type.value}"'
            output += f',\n\tdescription: "{tree_node.description}"'
            if tree_node.has_datatype():
                output += f',\n\tdatatype: "{tree_node.get_datatype()}"'
            if uuid:
                output += f',\n\tuuid: "{tree_node.uuid}"'
            if tree_node.has_unit():
                output += f',\n\tunit: "{tree_node.get_unit()}"'
            if tree_node.min is not None:
                output += f",\n\tmin: {tree_node.min}"
            if tree_node.max is not None:
                output += f",\n\tmax: {tree_node.max}"
            if tree_node.allowed:
                output += f",\n\tallowed: {tree_node.allowed}"

            output += "\n}"
    file.write(f"{output}")


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
    extended_attributes: str,
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
    print("Generating Franca output...")
    tree, datatype_tree = get_trees(
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
    outfile = open(output, "w")
    print_franca_header(outfile, franca_vss_version)
    print_franca_content(outfile, tree, uuid)
    outfile.write("\n]")
    outfile.close()
