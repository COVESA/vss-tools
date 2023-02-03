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

from enum import Enum
from vspec.model.vsstree import VSSNode
from vspec.model.constants import Unit
from vspec.loggingconfig import initLogging
import argparse
import logging
import sys
import vspec


from vspec.vssexporters import vss2json, vss2csv, vss2yaml, vss2binary, vss2franca, vss2ddsidl, vss2graphql


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
    idl = vss2ddsidl
    graphql = vss2graphql

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
    initLogging()

    parser.add_argument('-I', '--include-dir', action='append', metavar='dir', type=str, default=[],
                        help='Add include directory to search for included vspec files.')
    parser.add_argument('-e', '--extended-attributes', type=str, default="",
                        help='Whitelisted extended attributes as comma separated list. Note, that not all exporters will support (all) extended attributes.')
    parser.add_argument('-s', '--strict', action='store_true',
                        help='Use strict checking: Terminate when anything not covered or not recommended by VSS language or extensions is found.')
    parser.add_argument('--abort-on-unknown-attribute', action='store_true',
                        help=" Terminate when an unknown attribute is found.")
    parser.add_argument('--abort-on-name-style', action='store_true',
                        help=" Terminate naming style not follows recommendations.")
    parser.add_argument('--format', metavar='format', type=Exporter.from_string, choices=list(Exporter),
                        help='Output format, choose one from ' + str(Exporter._member_names_) + ". If omitted we try to guess form output_file suffix.")
    parser.add_argument('--uuid', action='store_true',
                        help='Include uuid in generated files. This is currently the default behavior.')
    parser.add_argument('--no-uuid', action='store_true',
                        help='Exclude uuid in generated files. This will be default behavior from VSS 4.0 onwards.')
    parser.add_argument('-o', '--overlays', action='append', metavar='overlays', type=str, default=[],
                        help='Add overlay that will be layered on top of the VSS file in the order they appear.')
    parser.add_argument('-u', '--unit-file', action='append', metavar='unit_file', type=str, default=[],
                        help='Unit file to be used for generation. Argument -u may be used multiple times.')
    parser.add_argument('vspec_file', metavar='<vspec_file>',
                        help='The vehicle specification file to convert.')
    parser.add_argument('output_file', metavar='<output_file>',
                        help='The file to write output to.')

    type_group = parser.add_argument_group(
        'VSS Data Type Tree arguments',
        'Arguments related to struct/type support [Experimental]')
    type_group.add_argument('-vt', '--vspec-types-file', metavar='vspec_types_file', type=str, required=False,
                            help='Data types file in vspec format.')
    type_group.add_argument('-ot', '--types-output-file', metavar='<types_output_file>',
                            help='Output file for writing data types from vspec file.')

    for entry in Exporter:
        entry.value.add_arguments(parser.add_argument_group(
            f"{entry.name.upper()} arguments", ""))

    args = parser.parse_args(arguments)

    # Figure out output format
    if args.format is not None:  # User has given format parameter
        logging.info("Output to " + str(args.format.name) + " format")
    else:  # Else try to figure from output file suffix
        try:
            suffix = args.output_file[args.output_file.rindex(".") + 1:]
        except BaseException:
            logging.error(
                "Can not determine output format. Try setting --format parameter")
            sys.exit(-1)
        try:
            args.format = Exporter.from_string(suffix)
        except BaseException:
            logging.error(
                "Can not determine output format. Try setting --format parameter")
            sys.exit(-1)

        logging.info("Output to " + str(args.format.name) + " format")

    include_dirs = ["."]
    include_dirs.extend(args.include_dir)

    abort_on_unknown_attribute = False
    abort_on_namestyle = False

    if args.abort_on_unknown_attribute or args.strict:
        abort_on_unknown_attribute = True
    if args.abort_on_name_style or args.strict:
        abort_on_namestyle = True

    known_extended_attributes_list = args.extended_attributes.split(",")
    if len(known_extended_attributes_list) > 0:
        vspec.model.vsstree.VSSNode.whitelisted_extended_attributes = known_extended_attributes_list
        logging.info(
            f"Known extended attributes: {', '.join(known_extended_attributes_list)}")

    exporter = args.format.value

    if args.uuid and args.no_uuid:
        logging.error("Can not use --uuid and --no-uuid at the same time")
        sys.exit(-1)
    if not (args.uuid or args.no_uuid):
        # From VSS 4.0 default shall be be False and a deprecation warning shall
        # be given no_uuid is used
        logging.warning(
            "From VSS 4.0 the default behavior for printing uuid will change. Consider using --uuid or --no-uuid.")
    print_uuid = True
    if args.no_uuid:
        print_uuid = False

    if not args.unit_file:
        logging.warning(
            "Use of default VSS unit file is deprecated, please specify the unit file you want to use with the -u argument!")
        Unit.load_default_config_file()
    else:
        for unit_file in args.unit_file:
            logging.info("Reading unit definitions from " + str(unit_file))
            Unit.load_config_file(unit_file)

    # process data type tree
    type_tree = None
    if args.vspec_types_file or args.types_output_file:
        type_tree = processDataTypeTree(parser, args)

    try:
        logging.info(f"Loading vspec from {args.vspec_file}...")
        tree = vspec.load_tree(
            args.vspec_file, include_dirs, break_on_unknown_attribute=abort_on_unknown_attribute, break_on_name_style_violation=abort_on_namestyle, expand_inst=False)

        for overlay in args.overlays:
            logging.info(f"Applying VSS overlay from {overlay}...")
            othertree = vspec.load_tree(overlay, include_dirs, break_on_unknown_attribute=abort_on_unknown_attribute,
                                        break_on_name_style_violation=abort_on_namestyle, expand_inst=False)
            vspec.merge_tree(tree, othertree)

        vspec.expand_tree_instances(tree)

        vspec.clean_metadata(tree)
        logging.info("Calling exporter...")
        exporter.export(args, tree, print_uuid)
        logging.info("All done.")
    except vspec.VSpecError as e:
        logging.error(f"Error: {e}")
        sys.exit(255)


def processDataTypeTree(parser: argparse.ArgumentParser, args) -> VSSNode:
    """
    Helper function to process command line arguments and invoke logic for processing data type information provided in vspec format
    """
    # check that both required arguments are available to process the data
    # type tree
    if args.types_output_file is None or args.vspec_types_file is None:
        parser.error(
            "Please provide the vspec data types file and the output file")

    logging.warning(
        "vspec struct/type support is an experimental feature. Not all features in the tool chain are supported. Proceed with caution")
    if len(args.overlays) > 0:
        parser.error(
            "Overlays are not yet supported in vspec struct/data type support feature")
    if args.format.name != "json":
        parser.error(
            f"{args.format_name} format is not yet supported in vspec struct/data type support feature")

    raise NotImplementedError(
        "vspec data type processing is not yet implemented")


if __name__ == "__main__":
    main(sys.argv[1:])
