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
from vspec.model.vsstree import VSSNode, VSSType
from anytree import PreOrderIter


def add_arguments(parser: argparse.ArgumentParser):
   parser.description="The csv exporter does not support any additional arguments."

#Write the header line
def print_csv_header(file, uuid):
    arg_list = ["Signal","Type","DataType","Deprecated","Unit","Min","Max","Desc","Comment","Allowed"]
    if uuid:
        arg_list.append("Id")
    file.write(format_csv_line(arg_list))

#Format a data or header line according to the CSV standard (IETF RFC 4180)
def format_csv_line(csv_fields):
    formatted_csv_line = ""
    for csv_field in csv_fields:
        formatted_csv_line = formatted_csv_line + '"' + str(csv_field).replace('"', '""') + '",'
    return formatted_csv_line[:-1] + '\n'

#Write the data lines
def print_csv_content(file, tree : VSSNode, uuid):
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.datatype.value if tree_node.has_datatype() else ""
        unit_str = tree_node.unit.value if tree_node.has_unit() else ""
        arg_list = [tree_node.qualified_name('.'),tree_node.type.value,data_type_str,tree_node.deprecation,unit_str,tree_node.min,tree_node.max,tree_node.description,tree_node.comment,tree_node.allowed]
        if uuid:
            arg_list.append(tree_node.uuid)
        file.write(format_csv_line(arg_list))


def export(config: argparse.Namespace, root: VSSNode, print_uuid):
    print("Generating CSV output...")
    outfile=open(config.output_file,'w')
    print_csv_header(outfile, print_uuid)
    print_csv_content(outfile, root, print_uuid)
    outfile.write("\n")
    outfile.close()
