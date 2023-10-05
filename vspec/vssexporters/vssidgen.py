#!/usr/bin/env python3
#
# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
#
# Generate IDs of 4bytes size, 3 bytes incremental value + 1 byte for layer id.

from vspec.model.vsstree import VSSNode
import argparse
import logging
from typing import Dict
import yaml
from vspec.loggingconfig import initLogging


def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument('--gen-ID-offset', type=int, default=1,
                        help="Offset for static ID values in YAML output (default is 1).")
    parser.add_argument('--gen-layer-ID-offset', type=int, default=0,
                        help="Define layer ID.")
    parser.add_argument('--gen-no-layer', action='store_true',
                    help="Generate static node ID without layer ID.")
    parser.add_argument('--gen-decimal-ID', action='store_true',
                    help="Generate static decimal ID of 3 bytes .")

    
# Function to generate a split ID (3 bytes for incremental number, 1 byte for layer)
def generate_split_id(node, id_counter, offset, layer, no_layer, decimal_output):
    node_id = (id_counter + offset) % 1000000  # Use 6 digits for the incremental number

    if decimal_output:
        return str(node_id).zfill(6), id_counter + 1  # Decimal output without layer
    else:
        if no_layer:
            return format((node_id), '06X'), id_counter + 1  # Hexadecimal output without layer
        else:
            if 0 <= layer <= 63:
                logging.warning("Layer value from 0 to 63 is reserved for COVESA.")
            layer = min(layer, 255)  # Use 1 byte for the layer (max_layer is 0-255)
            return format(((node_id << 8) | layer), '08X'), id_counter + 1  # Hexadecimal output with layer


def get_node_path(node):
    path = [node.name]
    while node.parent:
        node = node.parent
        path.insert(0, node.name)
    return ".".join(path)


def export_node(yaml_dict, node, id_counter, offset, layer, no_layer, decimal_output):

    node_id, id_counter = generate_split_id(node, id_counter, offset, layer, no_layer, decimal_output)

    node_path = get_node_path(node)
    
    if decimal_output:
        yaml_dict[node_path] = {"staticUID": node_id}  # Convert ID to a 3-digit decimal string
    else: 
        yaml_dict[node_path] = {"staticUID": f'0x{node_id}'}  # Convert ID to a 3-digit decimal string

    yaml_dict[node_path]["type"] = str(node.type.value)
    if node.unit:
        yaml_dict[node_path]["unit"] = str(node.unit.value)
    if node.is_signal() or node.is_property():
        yaml_dict[node_path]["datatype"] = node.data_type_str



    for child in node.children:
        id_counter, id_counter = export_node(yaml_dict, child, id_counter, offset, layer, no_layer, decimal_output)

    return id_counter, id_counter


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid):

    logging.info("Generating YAML output...")

    id_counter = 0  # Initialize the ID counter

    signals_yaml_dict: Dict[str, str] = {}  # Use str for ID values
    id_counter, _ = export_node(signals_yaml_dict, signal_root, id_counter, config.gen_ID_offset, config.gen_layer_ID_offset, config.gen_no_layer, config.gen_decimal_ID)

    with open(config.output_file, 'w') as f:
        yaml.dump(signals_yaml_dict, f)

if __name__ == "__main__":
    initLogging()