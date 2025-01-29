# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to JSON

import json
from pathlib import Path
from typing import Any

import rich_click as click

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode


def get_data(node: VSSNode, with_extra_attributes: bool = True, extended_attributes: tuple[str, ...] = ()):
    data = node.data.as_dict(with_extra_attributes, extended_attributes=extended_attributes)
    if len(node.children) > 0:
        data["children"] = {}
    for child in node.children:
        data["children"][child.name] = get_data(child)
    return data


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
@clo.pretty_print_opt
@clo.extend_all_attributes_opt
@click.pass_context
def cli(
    ctx,
    vspec: Path,
    outputradial: Path,
    outputsankey: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    types_output: Path | None,
    pretty: bool,
    extend_all_attributes: bool,
):
    """
    Export Stats.
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
        expand=expand,
    )
    log.info("Generating JSON output...")

    signals_data = {tree.name: get_data(tree, extend_all_attributes, extended_attributes)}

    if datatype_tree:
        types_data: dict[str, Any] = {datatype_tree.name: get_data(datatype_tree, extend_all_attributes)}
        if not types_output:
            log.info("Adding custom data types to signal dictionary")
            signals_data["ComplexDataTypes"] = types_data
        else:
            with open(types_output, "w") as f:
                json.dump(types_data, f, indent=2, sort_keys=True)


    # Define a function to recursively build the new JSON structure
    def build_json_structure(obj, parent_name=None):
        result = []
        for key, value in obj.items():
            item = {'name': key}
            if 'children' in value:
                item['children'] = build_json_structure(value['children'], key)
            else:
                for prop, prop_value in value.items():
                    if prop != 'children':
                        item[prop] = prop_value
            result.append(item)
        
        # Sort nodes with children to the top
        result.sort(key=lambda x: (not ('children' in x), x.get('type', '')))
        return result

    # Build the new JSON structure
    new_data = {
        'name': 'Vehicle',
        'type': 'Vehicle',
        'children': build_json_structure(signals_data['Vehicle']['children'])
    }

    with open(outputradial, "w") as f:
        json.dump(new_data, f, indent=2)

# import pandas as pd

# # vspec export csv -s VehicleSignalSpecification.vspec -o VSS_TableData.csv --no-expand    
# # Load the data into a DataFrame
# data_metadata = pd.read_csv('vss-6-metadata.csv')

# # Filter out rows containing 'branch'
# data_metadata = data_metadata[~data_metadata.isin(['branch']).any(axis=1)]

# # Get the list of remaining column names
# column_names = data_metadata.columns.tolist()
# print(column_names)

# # Extract the substring between the first and second delimiter "."
# data_metadata['Property'] = data_metadata['Type'].apply(
#     lambda x: "dynamic" if x in ["sensor", "actuator"] else "static"
# )



# # Define the column names to be dropped
# columns_to_drop = ['Signal', 'Desc', 'Deprecated', 
#                    'Unit', 'Min', 'Max', 'Allowed','Comment',
#                    'Default', 'Instances']
# data_metadata.drop(columns=columns_to_drop, inplace=True)
# data_metadata['Dummy'] = 0


# # Function to print unique values in each column
# def print_unique_values(data):
#     for column in data.columns:
#         unique_values = data[column].unique()
#         print(f"Unique values in column '{column}':")
#         print(unique_values)
#         print("-" * 50)

# # Rearrange columns by specifying the correct order
# columns_order = [ 'Property', 'Type', 'DataType', 'Dummy']
# data_metadata = data_metadata[columns_order]

# # Call the function
# print_unique_values(data_metadata)

# # Save the modified data into a new CSV file
# data_metadata.to_csv('sankey.csv', index=False)


# import pandas as pd
# from collections import Counter

# # The actual data for fallbacks
# template_data = {
#     'Type': ['Attribute', 'Branches', 'Sensors', 'Actuators'],
#     'V2': [78, 117, 203, 101],
#     'V3': [86, 117, 263, 128],
#     'V4': [97, 147, 286, 179],
#     'V5': [110, 131, 313, 195]
# }

# # vspec export csv -s VehicleSignalSpecification.vspec -o VSS_TableData.csv --no-expand    

# # Load the output DataFrame from the piechart.csv file
# output = pd.read_csv('piechartversions.csv')

# # Load the metadata
# metadata = pd.read_csv('vss-6-metadata.csv')

# # Convert the 'default' column to integers
# metadata['Default'] = pd.to_numeric(metadata['Default'], errors='coerce')

# # Extract the major version number
# major_version = None
# for index, row in metadata.iterrows():
#     if 'Vehicle.VersionVSS.Major' in row['Signal'] and row['Default'] > 5:
#         major_version = int(row['Default'])
#         break

# # Check the conditions and count the types
# if (major_version is not None):
    
#     # Count the types
#     type_counts = Counter(metadata['Type'])
#     counts = {
#         'Branches': type_counts.get('branch', 0),
#         'Sensors': type_counts.get('sensor', 0),
#         'Actuators': type_counts.get('actuator', 0),
#         'Attributes': type_counts.get('attribute', 0),
#     }
    
#     # Add a new column if it does not already exist
#     column_name = f'V{major_version}'
#     if column_name not in output.columns:
#         output[column_name] = pd.Series([counts['Attributes'], counts['Branches'], counts['Sensors'], counts['Actuators']])

# # Save the updated DataFrame back to piechart.csv
# output.to_csv('piechartversions.csv', index=False)

# print(output)

