#!/usr/bin/env python3

# (c) 2022 BMW Group
# (c) 2022 Robert Bosch GmbH
# (c) 2016 Jaguar Land Rover
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec files to various other formats
#

import argparse
from enum import Enum
import sys
import vspec

from vssexporters import vss2json, vss2csv, vss2yaml, vss2binary, vss2franca, vss2idl



class Exporter(Enum):
    """
    You can add new exporters here. Put the code in vssexporters and add it here
    See one of the existing exporters for an example.
    Mandatory functions are
    def add_arguments(parser: argparse.ArgumentParser)
    def export(config: argparse.Namespace, root: VSSNode):
    """
    json = vss2json
    csv = vss2csv
    yaml = vss2yaml
    binary = vss2binary
    franca = vss2franca
    idl = vss2idl

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return Exporter[s]
        except KeyError:
            raise ValueError()


parser = argparse.ArgumentParser(description="Convert vspec to other formats.")


def main(arguments):
    parser.add_argument('-I', '--include-dir', action='append',  metavar='dir', type=str,  default=[],
                        help='Add include directory to search for included vspec files.')
    parser.add_argument('-s', '--strict', action='store_true',
                        help='Use strict checking: Terminate when anything not covered or not recommended by the core VSS specs is found.')
    parser.add_argument('--abort-on-non-core-attribute', action='store_true',
                        help=" Terminate when non-core attribute is found.")
    parser.add_argument('--abort-on-name-style', action='store_true',
                        help=" Terminate naming style not follows recommendations.")
    parser.add_argument('--format', metavar='format', type=Exporter.from_string, choices=list(Exporter),
                        help='Output format, choose one from '+str(Exporter._member_names_)+". If omitted we try to guess form output_file suffix.")
    parser.add_argument('--no-uuid', action='store_true',
                        help='Exclude uuids from generated files.')
    parser.add_argument('-o', '--overlays', action='append',  metavar='overlays', type=str,  default=[],
                        help='Add overlays that will be layered on top of the VSS file in the order they appear.')
    parser.add_argument('vspec_file', metavar='<vspec_file>',
                        help='The vehicle specification file to convert.')
    parser.add_argument('output_file', metavar='<output_file>',
                        help='The file to write output to.')

    for entry in Exporter:
        entry.value.add_arguments(parser.add_argument_group(
            f"{entry.name.upper()} arguments", ""))

    args = parser.parse_args(arguments)

    # Figure out output format
    if args.format != None:  # User has given format parameter
        print("Output to "+str(args.format.name)+" format")
    else:  # Else try to figure from output file suffix
        try:
            suffix = args.output_file[args.output_file.rindex(".")+1:]
        except:
            print("Can not determine output format. Try setting --format parameter")
            sys.exit(-1)
        try:
            args.format = Exporter.from_string(suffix)
        except:
            print("Can not determine output format. Try setting --format parameter")
            sys.exit(-1)
        print("Output to "+str(args.format.name)+" format")

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    abort_on_non_core_attribute = False
    abort_on_namestyle = False

    if args.abort_on_non_core_attribute or args.strict:
        abort_on_non_core_attribute = True
    if args.abort_on_name_style or args.strict:
        abort_on_namestyle = True

    exporter = args.format.value

    try:
        print(f"Loading vspec from {args.vspec_file}...")
        tree = vspec.load_tree(
            args.vspec_file, include_dirs, merge_private=False, break_on_noncore_attribute=abort_on_non_core_attribute, break_on_name_style_violation=abort_on_namestyle, expand_inst=False)

        for overlay in args.overlays:
            print(f"Applying VSS overlay from {overlay}...")
            othertree = vspec.load_tree(overlay,include_dirs, merge_private=False, break_on_noncore_attribute=abort_on_non_core_attribute, break_on_name_style_violation=abort_on_namestyle, expand_inst=False)
            vspec.merge_tree(tree, othertree)
        
        vspec.expand_tree_instances(tree)

        print("Calling exporter...")
        exporter.export(args, tree)
        print("All done.")
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        sys.exit(255)


if __name__ == "__main__":
    main(sys.argv[1:])
