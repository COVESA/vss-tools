# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# General CONFIG variables
# Custom string, which we use to escape " and ' characters in VSS node description/comments
# Used in file_helper.write_graph_to_file to properly escape characters in filedata, before to write it to a file.


class Config:
    OUTPUT_NAMESPACE: str | None = None
    VSPEC_VERSION: str | None = None
    SPLIT_DEPTH: int | None = None
    SAMM_TYPE = "samm"
    SAMM_VERSION = "2.1.0"
    CUSTOM_ESCAPE_CHAR = "#V2E-ESC-CHAR#"


def init(output_namespace: str, vspec_version: str, split_depth: int):
    Config.OUTPUT_NAMESPACE = output_namespace
    Config.VSPEC_VERSION = vspec_version
    Config.SPLIT_DEPTH = split_depth if (type(split_depth) is int and split_depth > 0) else 1
