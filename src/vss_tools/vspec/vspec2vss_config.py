#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

class Vspec2VssConfig:
    """
    This class is intended to be a container for settings related to the conversion
    from *.vspec files to the internal VSS model as well as for some generic vspec2x features.
    A user may change settings before vspec2x.main is called.
    Then vspec2x will use those settings to control which command line arguments
    that will be accepted or considered, and based on those some of the settings in this
    file may be overridden.
    The config instance is later passed to the vss2x instance, so that it can consider
    the settings as well.
    """

    def __init__(self):
        """
        Setting default/recommended features for vss-tools.
        """

        # Input to model parsing

        # Is it possible to request that uuid shall be generated
        self.uuid_supported = True
        # Shall it be possible to specify which extended attributes to consider?
        self.extended_attributes_supported = True
        # Shall it be possible to give a type tree
        self.type_tree_supported = True
        # Is it supported to get type data generated to a separate file
        # Only relevant if self.type_tree_supported is True
        self.separate_output_type_file_supported = True

        # shall vspec2vss expand the model (by default)
        self.expand_model = True
        # if so shall there anyway be an option to NOT expand
        self.no_expand_option_supported = True

        # Is an output file required as part of command line arguments
        self.output_file_required = True

        # As of now we have only one type of nodes in the type tree
        # and that is structs, so if we support type tree we assume structs are supported

        # Default values for features
        # These are typically updated by vspec2x when reading command line arguments
        self.generate_uuid = False
