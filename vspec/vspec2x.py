

# Copyright (c) 2016 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert vspec files to various other formats
#

from vspec.model.vsstree import VSSNode
from vspec.model.constants import VSSTreeType
from vspec.loggingconfig import initLogging
from vspec.vss2x import Vss2X
from vspec.vspec2vss_config import Vspec2VssConfig
import argparse
import logging
import sys
import vspec

import pkg_resources  # part of setuptools
VERSION = pkg_resources.require("vss-tools")[0].version


class Vspec2X():
    """
    Framework for translating from *.vspec files to first an internal VSS model,
    and then to something else called X.
    Users must provide a Vss2X generator that can generate X if they get a VSS model as input.
    """
    def __init__(self, generator: Vss2X, vspec2vss_config: Vspec2VssConfig):

        self.generator = generator
        self.vspec2vss_config = vspec2vss_config

    def main(self, arguments):
        initLogging()
        parser = argparse.ArgumentParser(description="Convert vspec to other formats.")

        parser.add_argument('--version', action='version', version=VERSION)
        parser.add_argument('-I', '--include-dir', action='append', metavar='dir', type=str, default=[],
                            help='Add include directory to search for included vspec files.')
        if self.vspec2vss_config.extended_attributes_supported:
            parser.add_argument('-e', '--extended-attributes', type=str, default="",
                                help='Whitelisted extended attributes as comma separated list.')
        parser.add_argument('-s', '--strict', action='store_true',
                            help='Use strict checking: Terminate when anything not covered or not recommended '
                                 'by VSS language or extensions is found.')
        parser.add_argument('--abort-on-unknown-attribute', action='store_true',
                            help=" Terminate when an unknown attribute is found.")
        parser.add_argument('--abort-on-name-style', action='store_true',
                            help=" Terminate naming style not follows recommendations.")
        # For 4.X always keep uuid even if not considered fo backward compatibility
        parser.add_argument('--uuid', action='store_true',
                            help='Include uuid in generated files.')
        parser.add_argument('--no-uuid', action='store_true',
                            help='Exclude uuid in generated files.  This is currently the default behavior. ' +
                            ' This argument is deprecated and will be removed in VSS 5.0')
        if self.vspec2vss_config.expand_model and self.vspec2vss_config.no_expand_option_supported:
            parser.add_argument('--no-expand', action='store_true',
                                help='Do not expand tree.')
        parser.add_argument('-o', '--overlays', action='append', metavar='overlays', type=str, default=[],
                            help='Add overlay that will be layered on top of the VSS file in the order they appear.')
        parser.add_argument('-q', '--quantity-file', action='append', metavar='quantity_file', type=str, default=[],
                            help='Quantity file to be used for generation. Argument -q may be used multiple times.')
        parser.add_argument('-u', '--unit-file', action='append', metavar='unit_file', type=str, default=[],
                            help='Unit file to be used for generation. Argument -u may be used multiple times.')
        parser.add_argument('vspec_file', metavar='<vspec_file>',
                            help='The vehicle specification file to convert.')
        if self.vspec2vss_config.output_file_required:
            parser.add_argument('output_file', metavar='<output_file>',
                                help='The file to write output to.')

        if self.vspec2vss_config.type_tree_supported:
            type_group = parser.add_argument_group('VSS Data Type Tree arguments',
                                                   'Arguments related to struct/type support')

            type_group.add_argument('-vt', '--vspec-types-file', action='append', metavar='vspec_types_file', type=str,
                                    default=[],
                                    help='Data types file in vspec format.')
            if self.vspec2vss_config.separate_output_type_file_supported:
                # Note we might get some odd errors if using -ot in a tool not supporting it due to conflict with -o
                type_group.add_argument('-ot', '--types-output-file', metavar='<types_output_file>',
                                        help='Output file for writing data types from vspec file. ' +
                                        'If not specified, a single file is used where applicable. ' +
                                        'In case of JSON and YAML, the data is exported under a ' +
                                        'special key - "ComplexDataTypes"')

        self.generator.add_arguments(parser.add_argument_group(
            "Exporter specific arguments", ""))

        args = parser.parse_args(arguments)

        logging.info("VSS-tools version %s", VERSION)

        include_dirs = ["."]
        include_dirs.extend(args.include_dir)

        abort_on_unknown_attribute = False
        abort_on_namestyle = False

        if args.abort_on_unknown_attribute or args.strict:
            abort_on_unknown_attribute = True
        if args.abort_on_name_style or args.strict:
            abort_on_namestyle = True

        if self.vspec2vss_config.extended_attributes_supported:
            known_extended_attributes_list = args.extended_attributes.split(",")
            if len(known_extended_attributes_list) > 0:
                vspec.model.vsstree.VSSNode.whitelisted_extended_attributes = known_extended_attributes_list
                logging.info(f"Known extended attributes: {', '.join(known_extended_attributes_list)}")
        else:
            known_extended_attributes_list = list()

        if args.uuid and args.no_uuid:
            logging.error("Can not use --uuid and --no-uuid at the same time")
            sys.exit(-1)
        if args.no_uuid:
            logging.warning("The argument --no-uuid is deprecated and will be removed in VSS 5.0")

        self.vspec2vss_config.generate_uuid = self.vspec2vss_config.uuid_supported and args.uuid

        self.vspec2vss_config.expand_model = (self.vspec2vss_config.expand_model and not
                                              (self.vspec2vss_config.no_expand_option_supported and args.no_expand))

        vspec.load_quantities(args.vspec_file, args.quantity_file)
        vspec.load_units(args.vspec_file, args.unit_file)

        # process data type tree
        data_type_tree = None
        if self.vspec2vss_config.type_tree_supported:
            if self.vspec2vss_config.separate_output_type_file_supported:
                if args.types_output_file is not None and not args.vspec_types_file:
                    parser.error("An output file for data types was provided. Please also provide "
                                 "the input vspec file for data types")
            if args.vspec_types_file:
                data_type_tree = self.processDataTypeTree(
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
            if self.vspec2vss_config.expand_model:
                vspec.expand_tree_instances(tree)

            vspec.clean_metadata(tree)
            vspec.verify_mandatory_attributes(tree, abort_on_unknown_attribute)
            logging.info("Calling exporter...")

            self.generator.generate(args, tree, self.vspec2vss_config, data_type_tree)
            logging.info("All done.")
        except vspec.VSpecError as e:
            logging.error(f"Error: {e}")
            sys.exit(255)

    def processDataTypeTree(self, parser: argparse.ArgumentParser, args, include_dirs,
                            abort_on_namestyle: bool) -> VSSNode:
        """
        Helper function to process command line arguments and invoke logic for processing data
        type information provided in vspec format
        """
        if self.vspec2vss_config.separate_output_type_file_supported and \
           args.types_output_file is None:
            logging.info("Sensors and custom data types will be consolidated into one file.")

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
