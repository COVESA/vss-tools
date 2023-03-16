#!/usr/bin/env python3

# (c) 2022 Robert Bosch GmbH
# (c) 2021 BMW Group
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec tree to CSV


import argparse
import logging
from vspec.model.vsstree import VSSNode
from anytree import PreOrderIter  # type: ignore[import]
from vspec.loggingconfig import initLogging
from vspec.model.constants import VSSTreeType


def add_arguments(parser: argparse.ArgumentParser):
    parser.description = "The csv exporter does not support any additional arguments."

# Write the header line


def print_csv_header(file, uuid, tree_type: VSSTreeType):
    arg_list = ["Signal"] if tree_type == VSSTreeType.SIGNAL_TREE else ["Node"]
    arg_list.extend(["Type", "DataType", "Deprecated", "Unit", "Min", "Max", "Desc", "Comment", "Allowed", "Default"])
    if uuid:
        arg_list.append("Id")
    file.write(format_csv_line(arg_list))

# Format a data or header line according to the CSV standard (IETF RFC 4180)


def format_csv_line(csv_fields):
    formatted_csv_line = ""
    for csv_field in csv_fields:
        formatted_csv_line = formatted_csv_line + '"' + str(csv_field).replace('"', '""') + '",'
    return formatted_csv_line[:-1] + '\n'

# Write the data lines


def print_csv_content(file, tree: VSSNode, uuid):
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.get_datatype()
        unit_str = tree_node.get_unit()
        arg_list = [tree_node.qualified_name('.'), tree_node.type.value, data_type_str, tree_node.deprecation,
                    unit_str, tree_node.min, tree_node.max, tree_node.description, tree_node.comment,
                    tree_node.allowed, tree_node.default]
        if uuid:
            arg_list.append(tree_node.uuid)
        file.write(format_csv_line(arg_list))


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid, data_type_root: VSSNode):
    for root, outfile, tree_type in zip([signal_root, data_type_root],
                                        [config.output_file, config.types_output_file],
                                        [VSSTreeType.SIGNAL_TREE, VSSTreeType.DATA_TYPE_TREE]):
        if root is None:
            continue

        logging.info("Generating CSV output...")
        with open(outfile, 'w') as f:
            print_csv_header(f, print_uuid, tree_type)
            print_csv_content(f, root, print_uuid)


if __name__ == "__main__":
    initLogging()
