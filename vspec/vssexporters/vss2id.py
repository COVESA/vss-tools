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

import argparse
import logging
import os
from typing import Dict, Tuple
from vspec import load_tree
from vspec.model.constants import VSSTreeType
from vspec.loggingconfig import initLogging
from vspec.model.vsstree import VSSNode
from vspec.utils import vss2id_val
from vspec.utils.idgen_utils import fnv1_32_hash, fnv1_24_hash
import yaml


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--gen-ID-offset",
        type=int,
        default=1,
        help="Offset for static ID values in YAML output (default is 1).",
    )
    parser.add_argument(
        "--gen-layer-ID-offset", type=int, default=0, help="Define layer ID."
    )
    parser.add_argument(
        "--gen-no-layer",
        action="store_true",
        help="Generate static node ID without layer ID.",
    )
    parser.add_argument(
        "--gen-decimal-ID",
        action="store_true",
        help="Generate static decimal ID of 3 bytes .",
    )
    parser.add_argument(
        "--validate-static-uid", type=str, default="", help="Path to validation file."
    )
    parser.add_argument(
        "--validate-automatic-mode",
        action="store_true",
        help="Automatic mode for validation in case you don't want to manually "
        "choose a method for writing new static UIDs.",
    )
    parser.add_argument(
        "--only-validate-no-export",
        action="store_true",
        default=False,
        help="For pytests and pipelines you can skip the export of the",
    )
    parser.add_argument(
        "--use-fnv1-hash",
        action="store_true",
        default=False,
        help="Use 32bit fnv1 hash for static UID",
    )


def generate_split_id(
    node, id_counter, offset, layer, no_layer, decimal_output, use_fnv1_hash
) -> Tuple[str, int]:
    """Function to generate a split ID (3 bytes for incremental number, 1 byte for layer)"""
    node_id = (id_counter + offset) % 1000000  # Use 6 digits for the incremental number

    if use_fnv1_hash:
        hashed_str: str
        if no_layer:
            hashed_str = format(fnv1_32_hash(node), "08X")
        else:
            if 0 <= layer <= 63:
                logging.warning("Layer value from 0 to 63 is reserved for COVESA.")
            elif layer > 255:
                logging.warning(
                    "Layer value over 255. 1 byte max! Using max value of 255"
                )
            layer = min(layer, 255)  # Use 1 byte for the layer (max_layer is 0-255)
            hashed_str = format(fnv1_24_hash(node) << 8 | layer, "08X")
        return hashed_str, id_counter + 1
    else:
        if decimal_output:
            return str(node_id).zfill(6), id_counter + 1  # Decimal output without layer
        else:
            if no_layer:
                return (
                    format(node_id, "06X"),
                    id_counter + 1,
                )  # Hexadecimal output without layer
            else:
                if 0 <= layer <= 63:
                    logging.warning("Layer value from 0 to 63 is reserved for COVESA.")
                layer = min(layer, 255)  # Use 1 byte for the layer (max_layer is 0-255)
                return (
                    format(((node_id << 8) | layer), "08X"),
                    id_counter + 1,
                )  # Hexadecimal output with layer


def export_node(
    yaml_dict, node, id_counter, offset, layer, no_layer, decimal_output, use_fnv1_hash
):
    node_id, id_counter = generate_split_id(
        node, id_counter, offset, layer, no_layer, decimal_output, use_fnv1_hash
    )

    node_path = node.qualified_name()

    if decimal_output:
        # ToDo: why are some decimal IDs written with/without quotes
        yaml_dict[node_path] = {"staticUID": str(node_id)}
    else:
        yaml_dict[node_path] = {"staticUID": f"0x{node_id}"}
    yaml_dict[node_path]["description"] = node.description
    yaml_dict[node_path]["type"] = str(node.type.value)
    if node.unit:
        yaml_dict[node_path]["unit"] = str(node.unit.value)
    if node.is_signal() or node.is_property():
        yaml_dict[node_path]["datatype"] = node.data_type_str

    # ToDo proper constant for fka when accepted
    if "fka" in node.extended_attributes.keys():
        yaml_dict[node_path]["fka"] = node.extended_attributes["fka"]

    for child in node.children:
        id_counter, id_counter = export_node(
            yaml_dict,
            child,
            id_counter,
            offset,
            layer,
            no_layer,
            decimal_output,
            use_fnv1_hash,
        )

    return id_counter, id_counter


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid):
    logging.info("Generating YAML output...")

    id_counter = 0  # Initialize the ID counter

    signals_yaml_dict: Dict[str, str] = {}  # Use str for ID values
    id_counter, _ = export_node(
        signals_yaml_dict,
        signal_root,
        id_counter,
        config.gen_ID_offset,
        config.gen_layer_ID_offset,
        config.gen_no_layer,
        config.gen_decimal_ID,
        config.use_fnv1_hash,
    )

    if config.validate_static_uid:
        logging.info(
            f"Now validating nodes, static UIDs, types, units and description with "
            f"file '{config.validate_static_uid}'"
        )
        if os.path.isabs(config.validate_static_uid):
            other_path = config.validate_static_uid
        else:
            other_path = os.path.join(os.getcwd(), config.validate_static_uid)
        # ToDo: how do we know here if SIGNAL or DATA_TYPE tree
        validation_tree = load_tree(
            other_path, ["."], tree_type=VSSTreeType.SIGNAL_TREE
        )
        vss2id_val.validate_static_uids(signals_yaml_dict, validation_tree, config)

    if not config.only_validate_no_export:
        with open(config.output_file, "w") as f:
            yaml.dump(signals_yaml_dict, f)


if __name__ == "__main__":
    initLogging()
