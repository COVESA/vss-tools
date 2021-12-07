#!/usr/bin/env python3

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

#
# Convert vspec file to CSV
#

import sys

from anytree import PreOrderIter

import vspec
import argparse

from vspec.model.vsstree import VSSNode



#Format a data or header line according to the CSV standard (IETF RFC 4180)
def format_csv_line(*csv_fields):
    formatted_csv_line = ""
    for csv_field in csv_fields:
        formatted_csv_line = formatted_csv_line + '"' + str(csv_field).replace('"', '""') + '",'
    return formatted_csv_line[:-1] + '\n'

#Write the header line
def print_csv_header(file):
    file.write(format_csv_line("Signal","Type","DataType","Deprecated","Unit","Min","Max","Desc","Comment","Enum","Id"))

#Write the data lines
def print_csv_content(file, tree):
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.data_type.value if tree_node.has_data_type() else ""
        unit_str = tree_node.unit.value if tree_node.has_unit() else ""

        file.write(format_csv_line(
            tree_node.qualified_name('.'),tree_node.type.value,data_type_str,tree_node.deprecation,unit_str,tree_node.min,tree_node.max,tree_node.description,tree_node.comment,tree_node.enum,tree_node.uuid))


if __name__ == "__main__":
    # The arguments we accept

    parser = argparse.ArgumentParser(description='Convert vspec to csv.')
    parser.add_argument('-I', '--include-dir', action='append',  metavar='dir', type=str,
                    help='Add include directory to search for included vspec files.')
    parser.add_argument('-s', '--strict', action='store_true', help='Use strict checking: Terminate when non-core attribute is found.' )
    parser.add_argument('vspec_file', metavar='<vspec_file>', help='The vehicle specification file to convert.')
    parser.add_argument('csv_file', metavar='<csv file>', help='The file to output the CSV data to.')

    args = parser.parse_args()

    strict=args.strict

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    try:
        tree = vspec.load_tree(
            args.vspec_file, include_dirs, merge_private=False, break_on_noncore_attribute=strict)
        with open(args.csv_file, "w") as f:
            print_csv_header(f)
            print_csv_content(f, tree)
            f.write("\n")

    except vspec.VSpecError as e:
        print(f"Error: {e}")
        sys.exit(255)
