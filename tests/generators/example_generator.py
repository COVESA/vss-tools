#!/usr/bin/env python3
# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import sys
import logging
from vspec.model.vsstree import VSSNode
import argparse
from typing import Optional
from vspec.vss2x import Vss2X
from vspec.vspec2vss_config import Vspec2VssConfig
from vspec.vspec2x import Vspec2X


class ExampleGenerator(Vss2X):
    """
    This is an example on how easy you can write your own generator
    """

    def __init__(self, vspec2vss_config: Vspec2VssConfig):
        # Change default configs
        # By default Vspec2X requires that an output file is needed and specified
        # That is not needed for the ExampleGenerator as it just use stdout
        # By that reason we change default config to indicate that no output arguments is needed
        # That also implies that there will be an error if an output argument is specified
        vspec2vss_config.output_file_required = False

        # A lot of other things we do not care about, this reduces number or arguments shown
        # if you do "./example_generator.py --help"
        vspec2vss_config.uuid_supported = False
        vspec2vss_config.extended_attributes_supported = False
        vspec2vss_config.type_tree_supported = False

        # The rest here is generator-specific initializations
        self.count = 0

    def add_arguments(self, parser: argparse.ArgumentParser):
        """
        Add generator specific arguments
        """
        parser.add_argument('-k', '--keyword',
                            help="Phrase to search for", required=True)

    def handle_node(self, node: VSSNode):
        if self.keyword in str.lower(node.comment):
            self.count += 1
        for child in node.children:
            self.handle_node(child)

    def generate(self, config: argparse.Namespace, signal_root: VSSNode, vspec2vss_config: Vspec2VssConfig,
                 data_type_root: Optional[VSSNode] = None) -> None:
        """
        It is required to implement the generate method
        """
        self.keyword = str.lower(config.keyword)
        self.handle_node(signal_root)

        logging.info("Generating Example output...")
        logging.info("I found %d comments with %s", self.count, self.keyword)


if __name__ == "__main__":
    vspec2vss_config = Vspec2VssConfig()
    # The generator shall know nothing about vspec processing or vspec2vss arguments!
    # (Even if it may have some expectations on how the model look like)
    generator = ExampleGenerator(vspec2vss_config)
    vspec2x = Vspec2X(generator, vspec2vss_config)
    vspec2x.main(sys.argv[1:])
