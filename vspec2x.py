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
from vspec.model.constants import VSSTreeType
from vspec.loggingconfig import initLogging
import argparse
import logging
import sys
import vspec


from vspec.vssexporters import vss2json, vss2csv, vss2yaml, \
    vss2binary, vss2franca, vss2ddsidl, vss2graphql, vss2protobuf

SUPPORTED_STRUCT_EXPORT_FORMATS = set(["json", "yaml", "csv", "protobuf"])


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
    protobuf = vss2protobuf

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
                        help='Whitelisted extended attributes as comma separated list. '
                             'Note, that not all exporters will support (all) extended attributes.')
    parser.add_argument('-s', '--strict', action='store_true',
                        help='Use strict checking: Terminate when anything not covered or not recommended '
                             'by VSS language or extensions is found.')
    parser.add_argument('--abort-on-unknown-attribute', action='store_true',
                        help=" Terminate when an unknown attribute is found.")
    parser.add_argument('--abort-on-name-style', action='store_true',
                        help=" Terminate naming style not follows recommendations.")
    parser.add_argument('--format', metavar='format', type=Exporter.from_string, choices=list(Exporter),
                        help='Output format, choose one from ' +
                             str(Exporter._member_names_) +  # pylint: disable=no-member
                             ". If omitted we try to guess form output_file suffix.")
    parser.add_argument('--uuid', action='store_true',
                        help='Include uuid in generated files.')
    parser.add_argument('--no-uuid', action='store_true',
                        help='Exclude uuid in generated files.  This is currently the default behavior. ' +
                             ' This argument is deprecated and will be removed in VSS 5.0')
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
        'Arguments related to struct/type support')
    type_group.add_argument('-vt', '--vspec-types-file', action='append', metavar='vspec_types_file', type=str,
                            default=[],
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
    if args.no_uuid:
        logging.warning("The argument --no-uuid is deprecated and will be removed in VSS 5.0")
    print_uuid = False
    if args.uuid:
        print_uuid = True

    vspec.load_units(args.vspec_file, args.unit_file)

    # process data type tree
    if args.types_output_file is not None and not args.vspec_types_file:
        parser.error("An output file for data types was provided. Please also provide "
                     "the input vspec file for data types")
    data_type_tree = None
    if args.vspec_types_file:
        data_type_tree = processDataTypeTree(
            parser, args, include_dirs, abort_on_namestyle)
        vspec.verify_mandatory_attributes(data_type_tree, abort_on_unknown_attribute)

    try:
        logging.info(f"Loading vspec from {args.vspec_file}...")
        tree = vspec.load_tree(
            args.vspec_file, include_dirs, VSSTreeType.SIGNAL_TREE,
            break_on_name_style_violation=abort_on_namestyle,
            expand_inst=False, data_type_tree=data_type_tree)

        for overlay in args.overlays:
            logging.info(f"Applying VSS overlay from {overlay}...")
            othertree = vspec.load_tree(overlay, include_dirs, VSSTreeType.SIGNAL_TREE,
                                        break_on_name_style_violation=abort_on_namestyle, expand_inst=False,
                                        data_type_tree=data_type_tree)
            vspec.merge_tree(tree, othertree)

        vspec.check_type_usage(tree, VSSTreeType.SIGNAL_TREE, data_type_tree)
        vspec.expand_tree_instances(tree)

        vspec.clean_metadata(tree)
        vspec.verify_mandatory_attributes(tree, abort_on_unknown_attribute)
        logging.info("Calling exporter...")

        # temporary until all exporters support data type tree
        if args.format.name in SUPPORTED_STRUCT_EXPORT_FORMATS:
            exporter.export(args, tree, print_uuid, data_type_tree)
        else:
            if data_type_tree is not None:
                parser.error(
                    f"{args.format.name} format is not yet supported in vspec struct/data type support feature")
            exporter.export(args, tree, print_uuid)
        logging.info("All done.")
    except vspec.VSpecError as e:
        logging.error(f"Error: {e}")
        sys.exit(255)


def processDataTypeTree(parser: argparse.ArgumentParser, args, include_dirs,
                        abort_on_namestyle: bool) -> VSSNode:
    """
    Helper function to process command line arguments and invoke logic for processing data
    type information provided in vspec format
    """
    if args.types_output_file is None:
        logging.info("Sensors and custom data types will be consolidated into one file.")
        if args.format == Exporter.protobuf:
            logging.info("Proto files will be written to the current working directory")

    logging.warning("All exports do not yet support structs. Please check documentation for your exporter!")

    first_tree = True
    for type_file in args.vspec_types_file:
        logging.info(f"Loading and processing struct/data type tree from {type_file}")
        new_tree = vspec.load_tree(type_file, include_dirs, VSSTreeType.DATA_TYPE_TREE,
                                   break_on_name_style_violation=abort_on_namestyle, expand_inst=False)
        if first_tree:
            tree = new_tree
            first_tree = False
        else:
            vspec.merge_tree(tree, new_tree)
    vspec.check_type_usage(tree, VSSTreeType.DATA_TYPE_TREE)
    return tree


if __name__ == "__main__":
    main(sys.argv[1:])
