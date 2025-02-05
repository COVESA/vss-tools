# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to CSV

import csv
import pandas as pd
from pathlib import Path
from typing import Any

import rich_click as click
from anytree import PreOrderIter  # type: ignore[import]

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode
from vss_tools.utils.misc import getattr_nn
from collections import Counter


def get_header(entry_type: str, with_instance_column: bool) -> list[str]:
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
    if with_instance_column:
        row.append("Instances")
    return row


def add_rows(rows: list[list[Any]], root: VSSNode, with_instance_column: bool) -> None:
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
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path,
):
    """
    Export CSV Stats for Pie Chart.
    """
    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        expand=not expand,
    )
    log.info("Generating CSV output...")

    generic_entry = datatype_tree and not types_output
    with_instance_column = not expand

    entry_type = "Node" if generic_entry else "Signal"
    rows = [get_header(entry_type, with_instance_column)]
    add_rows(rows, tree, with_instance_column)
    if generic_entry and datatype_tree:
        add_rows(rows, datatype_tree, with_instance_column)




    if not generic_entry and datatype_tree:
        rows = [get_header("Node", with_instance_column)]
        add_rows(rows, datatype_tree, with_instance_column)

    data_metadata = pd.DataFrame(rows[1:], columns=rows[0])    

    # Now you generated:
    # vspec export csv -s VehicleSignalSpecification.vspec -o VSS_TableData.csv --no-expand
    #
    # The actual data of first 5 version for fallbacks
    # template_data = {
    #     'Type': ['Attribute', 'Branches', 'Sensors', 'Actuators'],
    #     'V2': [78, 117, 203, 101],
    #     'V3': [86, 117, 263, 128],
    #     'V4': [97, 147, 286, 179],
    #     'V5': [110, 131, 313, 195]
    # }

    latest = pd.read_csv('../vehicle_signal_specification/docs-gen/static/data/piechartnotexpanded.csv')

    metadata = data_metadata

    metadata['Default'] = pd.to_numeric(metadata['Default'], errors='coerce')

    major_version = None
    for index, row in metadata.iterrows():
        if 'Vehicle.VersionVSS.Major' in row['Signal'] and row['Default'] > 5:
            major_version = int(row['Default'])
            break

    if (major_version is not None):
        
        type_counts = Counter(metadata['Type'])
        counts = {
            'Branches': type_counts.get('branch', 0),
            'Sensors': type_counts.get('sensor', 0),
            'Actuators': type_counts.get('actuator', 0),
            'Attributes': type_counts.get('attribute', 0),
        }
        
        column_name = f'V{major_version}'
        if column_name not in latest.columns:
            latest[column_name] = pd.Series([counts['Attributes'], counts['Branches'], counts['Sensors'], counts['Actuators']])
        version_cols = [col for col in latest.columns if col.startswith('V')]
        for i in range(len(version_cols) - 1):
            v1 = int(version_cols[i][1])
            v2 = int(version_cols[i+1][1])
            if v2 != v1 + 1:
                print(f"MISSING VERSION: V{v1+1}")

    latest.to_csv(output, index=False)



