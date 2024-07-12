#!/usr/bin/env python3

# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to CSV


from pathlib import Path
from vss_tools import log
import rich_click as click
import vss_tools.vspec.cli_options as clo
from vss_tools.vspec.model.vsstree import VSSNode
from vss_tools.vspec.vssexporters.utils import get_trees
from anytree import PreOrderIter  # type: ignore[import]
from typing import AnyStr


# Write the header line


def print_csv_header(file, uuid, entry_type: AnyStr, include_instance_column: bool):
    arg_list = [
        entry_type,
        "Type",
        "DataType",
        "Deprecated",
        "Unit",
        "Min",
        "Max",
        "Desc",
        "Comment",
        "Allowed",
        "Default",
    ]
    if uuid:
        arg_list.append("Id")
    if include_instance_column:
        arg_list.append("Instances")
    file.write(format_csv_line(arg_list))


# Format a data or header line according to the CSV standard (IETF RFC 4180)


def format_csv_line(csv_fields):
    formatted_csv_line = ""
    for csv_field in csv_fields:
        if csv_field is None:
            csv_field = ""
        formatted_csv_line = (
            formatted_csv_line + '"' + str(csv_field).replace('"', '""') + '",'
        )
    return formatted_csv_line[:-1] + "\n"


# Write the data lines


def print_csv_content(file, tree: VSSNode, uuid, include_instance_column: bool):
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.get_datatype()
        unit_str = tree_node.get_unit()
        arg_list = [
            tree_node.qualified_name("."),
            tree_node.type.value,
            data_type_str,
            tree_node.deprecation,
            unit_str,
            tree_node.min,
            tree_node.max,
            tree_node.description,
            tree_node.comment,
            tree_node.allowed,
            tree_node.default,
        ]
        if uuid:
            arg_list.append(tree_node.uuid)
        if include_instance_column and tree_node.instances is not None:
            arg_list.append(tree_node.instances)
        file.write(format_csv_line(arg_list))


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.expand_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.types_output_opt
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path,
):
    """
    Export as CSV.
    """
    tree, datatype_tree = get_trees(
        include_dirs,
        aborts,
        strict,
        extended_attributes,
        uuid,
        quantities,
        vspec,
        units,
        types,
        types_output,
        overlays,
        expand,
    )
    log.info("Generating CSV output...")

    generic_entry = datatype_tree and types_output
    include_instance_column = not expand
    with open(output, "w") as f:
        signal_entry_type = "Node" if generic_entry else "Signal"
        print_csv_header(
            f,
            uuid,
            signal_entry_type,
            include_instance_column,
        )
        print_csv_content(f, tree, uuid, include_instance_column)
        if datatype_tree is not None and generic_entry is True:
            print_csv_content(
                f,
                datatype_tree,
                uuid,
                include_instance_column,
            )

    if datatype_tree is not None and generic_entry is False:
        with open(types_output, "w") as f:
            print_csv_header(f, uuid, "Node", include_instance_column)
            print_csv_content(
                f,
                datatype_tree,
                uuid,
                include_instance_column,
            )
