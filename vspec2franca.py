#!/usr/bin/env python3

#
# (C) 2016 Jaguar Land Rover
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec file to FrancaIDL spec.
#

import sys
import vspec
import argparse


def traverse_tree(tree, outf, prefix_arr, is_first_element):
    # Convert a prefix array of path elements to a string
    def prefix_to_string(prefix_arr):
        if len(prefix_arr) == 0:
            return ""

        res = prefix_arr[0]
        for elem in prefix_arr[1:]:
            res = "{}.{}".format(res, elem)

        return res


    # Traverse all elemnts in tree.
    for key, val in tree.items():
        # Is this a branch?
        if "children" in val:
            # Yes. Recurse
            traverse_tree(val['children'], outf, prefix_arr + [ key ], is_first_element)
            continue

        # Drop a comma in before the next element.
        if not is_first_element:
            outf.write(",\n")

        outf.write("""{{
    name: "{}"
    type: "{}"
    description: "{}"
""".format(prefix_to_string(prefix_arr + [ key ]),
           val['type'],
           val['description']))

        if "datatype" in val:
            outf.write("    datatype: {}\n".format(val["datatype"]))

        if "uuid" in val:
            outf.write("    uuid: {}\n".format(val["uuid"]))

        if "min" in val:
            outf.write("    min: {}\n".format(val["min"]))

        if "max" in val:
            outf.write("    max: {}\n".format(val["max"]))

        if "unit" in val:
            outf.write("    unit: {}\n".format(val["unit"]))

        if "allowed" in val:
            outf.write("    allowed: {}\n".format(val["allowed"]))

        if "sensor" in val:
            outf.write("    sensor: {}\n".format(val["sensor"]))

        if "actuator" in val:
            outf.write("    actuator: {}\n".format(val["actuator"]))

        outf.write("}\n")
        is_first_element = False


if __name__ == "__main__":
    # The arguments we accept

    parser = argparse.ArgumentParser(description='Convert vspec to franca.')
    parser.add_argument('-I', '--include-dir', action='append',  metavar='dir', type=str, default=[],
                    help='Add include directory to search for included vspec files.')
    parser.add_argument('-s', '--strict', action='store_true', help='Use strict checking: Terminate when non-core attribute is found.' )
    parser.add_argument('-v', '--vssversion', type=str, default="unspecified version",  help='VSS version' )
    parser.add_argument('vspec_file', metavar='<vspec_file>', help='The vehicle specification file to convert.')
    parser.add_argument('franca_file', metavar='<franca file>', help='The file to output the Franca IDL spec to.')

    args = parser.parse_args()

    strict=args.strict
    
    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    franca_out = open(args.franca_file, "w")

    
    try:
        tree = vspec.load(args.vspec_file, include_dirs)
    except vspec.VSpecError as e:
        print("Error: {}".format(e))
        sys.exit(255)

    franca_out.write(
"""// Copyright (C) 2016, GENIVI Alliance
//
// This program is licensed under the terms and conditions of the
// Mozilla Public License, version 2.0.  The full text of the
// Mozilla Public License is at https://www.mozilla.org/MPL/2.0/

const UTF8String VSS_VERSION = "{}"

struct SignalSpec {{
    UInt32 id
    String name
    String type
    String description
}}

const SignalSpec[] signal_spec = [
""".format(args.vssversion))

    traverse_tree(tree, franca_out, [], True)

    franca_out.write(
"""
]
""")

    franca_out.close()
