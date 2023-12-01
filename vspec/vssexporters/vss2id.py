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
import sys
from typing import Dict, Tuple
from vspec import load_tree
from vspec.model.constants import VSSTreeType
from vspec.loggingconfig import initLogging
from vspec.model.vsstree import VSSNode
from vspec.utils import vss2id_val
from vspec.utils.idgen_utils import (
    get_node_identifier_bytes,
    fnv1_32_hash,
    get_all_keys_values,
)
import yaml


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Adds command line arguments to a pre-existing argument parser

    @param parser: the pre-existing argument parser
    """
    parser.add_argument(
        "--validate-static-uid", type=str, default="", help="Path to validation file."
    )
    parser.add_argument(
        "--only-validate-no-export",
        action="store_true",
        default=False,
        help="For pytests and pipelines you can skip the export of the vspec file.",
    )


def generate_split_id(node: VSSNode, id_counter: int) -> Tuple[str, int]:
    """Generates static UIDs using 4-byte FNV-1 hash.

    @param node: VSSNode that we want to generate a static UID for
    @param id_counter: consecutive numbers counter for amount of nodes
    @return: tuple of hashed string and id counter
    """

    identifier = get_node_identifier_bytes(
        node.qualified_name(),
        node.data_type_str,
        node.type.value,
        node.get_unit(),
        node.allowed,
        node.min,
        node.max,
    )
    hashed_str = format(fnv1_32_hash(identifier), "08X")

    return hashed_str, id_counter + 1


def export_node(yaml_dict, node, id_counter) -> Tuple[int, int]:
    """Recursive function to export the full tree to a dict

    @param yaml_dict: the to be exported dict
    @param node: parent node of the tree
    @param id_counter: counter for amount of ids
    @return: id_counter, id_counter
    """
    node_id, id_counter = generate_split_id(node, id_counter)

    # check for hash duplicates
    for key, value in get_all_keys_values(yaml_dict):
        if not isinstance(value, dict) and key == "staticUID":
            if node_id == value[2:]:
                logging.fatal(
                    f"There is a small chance that the result of FNV-1 "
                    f"hashes are the same in this case the hash of node "
                    f"'{node.qualified_name()}' is the same as another hash."
                    f"Can you please update it."
                )
                # We could add handling of duplicates here
                sys.exit(-1)

    node_path = node.qualified_name()

    yaml_dict[node_path] = {"staticUID": f"0x{node_id}"}
    yaml_dict[node_path]["description"] = node.description
    yaml_dict[node_path]["type"] = str(node.type.value)
    if node.unit:
        yaml_dict[node_path]["unit"] = str(node.unit.value)
    if node.is_signal() or node.is_property():
        yaml_dict[node_path]["datatype"] = node.data_type_str
    if node.allowed:
        yaml_dict[node_path]["allowed"] = node.allowed
    if node.min:
        yaml_dict[node_path]["min"] = node.min
    if node.max:
        yaml_dict[node_path]["max"] = node.max

    if node.fka:
        yaml_dict[node_path]["fka"] = node.fka
    elif "fka" in node.extended_attributes.keys():
        yaml_dict[node_path]["fka"] = node.extended_attributes["fka"]

    if node.deprecation:
        yaml_dict[node_path]["deprecation"] = node.deprecation

    for child in node.children:
        id_counter, id_counter = export_node(
            yaml_dict,
            child,
            id_counter,
        )

    return id_counter, id_counter


def export(config: argparse.Namespace, signal_root: VSSNode, print_uuid):
    """Main export function used to generate the output id vspec.

    @param config: Command line arguments it was run with
    @param signal_root: root of the signal tree
    @param print_uuid: Not used here but needed by main script
    """
    logging.info("Generating YAML output...")

    id_counter: int = 0
    signals_yaml_dict: Dict[str, str] = {}  # Use str for ID values
    id_counter, _ = export_node(signals_yaml_dict, signal_root, id_counter)

    if config.validate_static_uid:
        logging.info(
            f"Now validating nodes, static UIDs, types, units and description with "
            f"file '{config.validate_static_uid}'"
        )
        if os.path.isabs(config.validate_static_uid):
            other_path = config.validate_static_uid
        else:
            other_path = os.path.join(os.getcwd(), config.validate_static_uid)

        validation_tree = load_tree(
            other_path, ["."], tree_type=VSSTreeType.SIGNAL_TREE
        )
        vss2id_val.validate_static_uids(signals_yaml_dict, validation_tree, config)

    if not config.only_validate_no_export:
        with open(config.output_file, "w") as f:
            yaml.dump(signals_yaml_dict, f)


if __name__ == "__main__":
    initLogging()
