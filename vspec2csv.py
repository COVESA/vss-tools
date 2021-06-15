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

from anytree import RenderTree, PreOrderIter

import vspec
import getopt

from vspec.model.vsstree import VSSNode


def usage():
    print(f"""
Usage: {sys.argv[0]} [options] vspec_file csv_file

  where [options] are:

  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple timees.

  -i prefix:uuid_file  "prefix" is an optional string that will be
                       prepended to each signal name defined in the
                       vspec file.

                       "uuid_file" is the name of the file containing the
                       static UUID values for the signals.  This file is
                       read/write and will be updated if necessary.

                       This option can be specified several times in
                       to store the UUIDs of different parts of the
                       signal tree in different files.

  vspec_file           The vehicle specification file to parse.

  csv_file             The file to output the CSV data to.
""")
    sys.exit(255)

#Format a data or header line according to the CSV standard (IETF RFC 4180)
def format_csv_line(*csv_fields):
    formatted_csv_line = ""
    for csv_field in csv_fields:
        formatted_csv_line = formatted_csv_line + '"' + str(csv_field).replace('"', '""') + '",'
    return formatted_csv_line[:-1] + '\n'

#Write the header line
def print_csv_header(file):
    file.write(format_csv_line("Signal","Type","DataType","Deprecated","Complex","Unit","Min","Max","Desc","Enum","Id","Instance"))

#Write the data lines
def print_csv_content(file, tree):
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.data_type.value if tree_node.has_data_type() else ""
        unit_str = tree_node.unit.value if tree_node.has_unit() else ""

        if tree_node.instances:
            for instance in tree_node.instances:
                file.write(format_csv_line(
                    tree_node.qualified_name('.'),tree_node.type.value,data_type_str,tree_node.deprecation,"true",unit_str,tree_node.min,tree_node.max,tree_node.description,tree_node.enum,tree_node.uuid,instance))
        else:
            file.write(format_csv_line(
                tree_node.qualified_name('.'),tree_node.type.value,data_type_str,tree_node.deprecation,"false",unit_str,tree_node.min,tree_node.max,tree_node.description,tree_node.enum,tree_node.uuid))


if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        else:
            usage()

    if len(args) != 2:
        usage()

    try:
        tree = vspec.load_tree(args[0], include_dirs)
        csv_out = open(args[1], "w")
        print_csv_header(csv_out)
        print_csv_content(csv_out, tree)
        csv_out.write("\n")
        csv_out.close()
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)
