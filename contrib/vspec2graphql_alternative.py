#!/usr/bin/env python3

#
# Copyright (C) 2022, Bayerische Motoren Werke Aktiengesellschaft (BMW AG)
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec file to graphql schema
#



import sys
import os
#Add path to main py vspec  parser
myDir= os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, ".."))

import vspec
import getopt
from vspec2graphql.traverse_tree import get_schema_from_tree


def usage():
    print(
        "Usage:",
        sys.argv[0],
        "[-I include_dir] ... [-i prefix:id_file] vspec_file json_file",
    )
    print("  -I include_dir       Add include directory to search for included vspec")
    print("                       files. Can be used multiple times.")
    print()
    print(
        "  -i prefix:uuid_file  File to use for storing generated UUIDs for signals with"
    )
    print(
        "                       a given path prefix. Can be used multiple times to store"
    )
    print("                       UUIDs for signal sub-trees in different files.")
    print()
    print(" vspec_file            The vehicle specification file to parse.")
    print(" graphql_schema        The file to output the graphql schema to.")
    sys.exit(255)


if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:i:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        elif o == "-i":
            id_spec = a.split(":")
            if len(id_spec) != 2:
                print("ERROR: -i needs a 'prefix:id_file' argument.")
                usage()

            [prefix, file_name] = id_spec
            vspec.db_mgr.create_signal_uuid_db(prefix, file_name)
        else:
            usage()

    if len(args) != 2:
        usage()

    with open(args[1], "w") as graphql_schema:
        try:
            tree = vspec.load_tree(args[0], include_dirs)
            graphql_schema.write(get_schema_from_tree(tree))

        except vspec.VSpecError as e:
            print("Error: {}".format(e))
            exit(255)
