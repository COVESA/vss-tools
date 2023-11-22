#!/usr/bin/env python3

# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to franca


import argparse
from typing import Optional
from vspec.model.vsstree import VSSNode
from anytree import PreOrderIter  # type: ignore[import]
from vspec.vss2x import Vss2X
from vspec.vspec2vss_config import Vspec2VssConfig


# Write the header line


def print_franca_header(file, version="unknown"):
    file.write(f"""
// Copyright (C) 2022, COVESA
//
// This program is licensed under the terms and conditions of the
// Mozilla Public License, version 2.0.  The full text of the
// Mozilla Public License is at https://www.mozilla.org/MPL/2.0/

const UTF8String VSS_VERSION = "{version}"

struct SignalSpec {{
    UInt32 id
    String name
    String type
    String description
    String datatype
    String unit
    Double min
    Double max
}}

const SignalSpec[] signal_spec = [
""")


# Write the data lines
def print_franca_content(file, tree, uuid):
    output = ""
    for tree_node in PreOrderIter(tree):
        if tree_node.parent:
            if output:
                output += ",\n{"
            else:
                output += "{"
            output += f"\tname: \"{tree_node.qualified_name('.')}\""
            output += f",\n\ttype: \"{tree_node.type.value}\""
            output += f",\n\tdescription: \"{tree_node.description}\""
            if tree_node.has_datatype():
                output += f",\n\tdatatype: \"{tree_node.get_datatype()}\""
            if uuid:
                output += f",\n\tuuid: \"{tree_node.uuid}\""
            if tree_node.has_unit():
                output += f",\n\tunit: \"{tree_node.get_unit()}\""
            if tree_node.min:
                output += f",\n\tmin: {tree_node.min}"
            if tree_node.max:
                output += f",\n\tmax: {tree_node.max}"
            if tree_node.allowed:
                output += f",\n\tallowed: {tree_node.allowed}"

            output += "\n}"
    file.write(f"{output}")


class Vss2Franca(Vss2X):

    def __init__(self, vspec2vss_config: Vspec2VssConfig):
        vspec2vss_config.no_expand_option_supported = False
        vspec2vss_config.type_tree_supported = False

    def add_arguments(self, parser: argparse.ArgumentParser):
        # Renamed from -v to --franca-vss-version to avoid conflict when using
        # -vt (Otherwise -vt would be interpreted as "-v t")
        parser.add_argument('--franca-vss-version', metavar='franca_vss_version',
                            help=" Add version information to franca file.")

    def generate(self, config: argparse.Namespace, signal_root: VSSNode, vspec2vss_config: Vspec2VssConfig,
                 data_type_root: Optional[VSSNode] = None) -> None:
        print("Generating Franca output...")
        outfile = open(config.output_file, 'w')
        print_franca_header(outfile, config.franca_vss_version)
        print_franca_content(outfile, signal_root, vspec2vss_config.generate_uuid)
        outfile.write("\n]")
        outfile.close()
