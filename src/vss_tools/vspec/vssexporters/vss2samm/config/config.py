# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# General CONFIG variables
SAMM_TYPE = "samm"
SAMM_VERSION = "2.1.0"
# Custom string, which we use to escape " and ' characters in VSS node description/comments
# Used in file_helper.write_graph_to_file to properly escape characters in filedata, before to write it to a file.
CUSTOM_ESCAPE_CHAR = "#V2E-ESC-CHAR#"

# CONFIG Variable defined at runtime as per user input and in available init function
OUTPUT_NAMESPACE = None
VSPEC_VERSION = None
SPLIT_DEPTH = None


def init(output_namespace: str, vspec_version: str, split_depth: int):
    # Set user defined or OUTPUT_NAMESPACE
    global OUTPUT_NAMESPACE
    OUTPUT_NAMESPACE = output_namespace

    # Set user defined or OUTPUT_NAMESPACE
    global VSPEC_VERSION
    VSPEC_VERSION = vspec_version

    # Make sure that split_depth is in correct type and value, else set it to DEFAULT: 1
    global SPLIT_DEPTH
    SPLIT_DEPTH = split_depth if (type(split_depth) is int and split_depth > 0) else 1
