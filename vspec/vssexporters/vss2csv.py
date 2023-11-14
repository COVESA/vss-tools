#!/usr/bin/env python3

# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to CSV


import argparse
import logging
from vspec.model.vsstree import VSSNode
from anytree import PreOrderIter  # type: ignore[import]
from vspec.loggingconfig import initLogging
from typing import AnyStr


def feature_supported(feature_name: str):
    """Return true for supported arguments/features"""
    if feature_name in ['no_expand']:
        return True
    return False


def add_arguments(parser: argparse.ArgumentParser):
    parser.description = "The csv exporter does not support any additional arguments."

# Write the header line


def print_csv_header(file, uuid, entry_type: AnyStr, include_instance_column: bool):
    arg_list = [entry_type, "Type", "DataType", "Deprecated", "Unit",
                "Min", "Max", "Desc", "Comment", "Allowed", "Default"]
    if uuid:
        arg_list.append("Id")
    if include_instance_column:
        arg_list.append("Instances")
    file.write(format_csv_line(arg_list))

# Format a data or header line according to the CSV standard (IETF RFC 4180)


def format_csv_line(csv_fields):
    formatted_csv_line = ""
    for csv_field in csv_fields:
        formatted_csv_line = formatted_csv_line + '"' + str(csv_field).replace('"', '""') + '",'
    return formatted_csv_line[:-1] + '\n'

# Write the data lines


def print_csv_content(file, tree: VSSNode, uuid, include_instance_column: bool):
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.get_datatype()
        unit_str = tree_node.get_unit()
        arg_list = [tree_node.qualified_name('.'), tree_node.type.value, data_type_str, tree_node.deprecation,
                    unit_str, tree_node.min, tree_node.max, tree_node.description, tree_node.comment,
                    tree_node.allowed, tree_node.default]
        if uuid:
            arg_list.append(tree_node.uuid)
        if include_instance_column and tree_node.instances is not None:
            arg_list.append(tree_node.instances)
        file.write(format_csv_line(arg_list))


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid, data_type_root: VSSNode):
    logging.info("Generating CSV output...")

    # generic entry should be written when both data types and signals are being written to the same file
    generic_entry = data_type_root is not None and config.types_output_file is None
    with open(config.output_file, 'w') as f:
        signal_entry_type = "Node" if generic_entry else "Signal"
        print_csv_header(f, print_uuid, signal_entry_type, config.no_expand)
        print_csv_content(f, signal_root, print_uuid, config.no_expand)
        if data_type_root is not None and generic_entry is True:
            print_csv_content(f, data_type_root, print_uuid, config.no_expand)

    if data_type_root is not None and generic_entry is False:
        with open(config.types_output_file, 'w') as f:
            print_csv_header(f, print_uuid, "Node", config.no_expand)
            print_csv_content(f, data_type_root, print_uuid, config.no_expand)


if __name__ == "__main__":
    initLogging()
