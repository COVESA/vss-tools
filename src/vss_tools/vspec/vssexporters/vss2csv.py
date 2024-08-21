# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to CSV

import csv
from pathlib import Path
from typing import Any

import rich_click as click
from anytree import PreOrderIter  # type: ignore[import]

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode
from vss_tools.vspec.utils.misc import getattr_nn


def get_header(with_uuid: bool, entry_type: str, with_instance_column: bool) -> list[str]:
    row = [
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
    if with_uuid:
        row.append("Id")
    if with_instance_column:
        row.append("Instances")
    return row


def add_rows(rows: list[list[Any]], root: VSSNode, with_uuid: bool, with_instance_column: bool) -> None:
    node: VSSNode
    for node in PreOrderIter(root):
        data = node.get_vss_data()
        row = [
            node.get_fqn(),
            data.type.value,
            getattr_nn(data, "datatype", ""),
            getattr_nn(data, "deprecation", ""),
            getattr_nn(data, "unit", ""),
            getattr_nn(data, "min", ""),
            getattr_nn(data, "max", ""),
            data.description,
            getattr_nn(data, "comment", ""),
            getattr_nn(data, "allowed", ""),
            getattr_nn(data, "default", ""),
        ]
        if with_uuid:
            row.append(getattr_nn(node, "uuid", ""))
        if with_instance_column:
            row.append(getattr_nn(data, "instances", ""))
        rows.append(row)


def write_csv(rows: list[list[Any]], output: Path):
    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


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
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        uuid=uuid,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        expand=expand,
    )
    log.info("Generating CSV output...")

    generic_entry = datatype_tree and not types_output
    with_instance_column = not expand

    entry_type = "Node" if generic_entry else "Signal"
    rows = [get_header(uuid, entry_type, with_instance_column)]
    add_rows(rows, tree, uuid, with_instance_column)
    if generic_entry and datatype_tree:
        add_rows(rows, datatype_tree, uuid, with_instance_column)
    write_csv(rows, output)

    if not generic_entry and datatype_tree:
        rows = [get_header(uuid, "Node", with_instance_column)]
        add_rows(rows, datatype_tree, uuid, with_instance_column)
        write_csv(rows, types_output)
