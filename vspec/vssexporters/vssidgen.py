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

from anytree import PreOrderIter  # type: ignore
import argparse
from enum import Enum
import logging
import os
from typing import Dict
from vspec import load_tree
from vspec.model.constants import VSSTreeType
from vspec.loggingconfig import initLogging
from vspec.model.vsstree import VSSNode
import yaml


class OverwriteMethod(Enum):
    ASSIGN_NEW_ID = 1
    OVERWRITE_ID_WITH_VALIDATION_ID = 2


def add_arguments(parser: argparse.ArgumentParser):
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


# Function to generate a split ID (3 bytes for incremental number, 1 byte for layer)
def generate_split_id(node, id_counter, offset, layer, no_layer, decimal_output):
    node_id = (id_counter + offset) % 1000000  # Use 6 digits for the incremental number

    if decimal_output:
        return str(node_id).zfill(6), id_counter + 1  # Decimal output without layer
    else:
        if no_layer:
            return (
                format((node_id), "06X"),
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


def export_node(yaml_dict, node, id_counter, offset, layer, no_layer, decimal_output):
    node_id, id_counter = generate_split_id(
        node, id_counter, offset, layer, no_layer, decimal_output
    )

    node_path = node.qualified_name()

    if decimal_output:
        yaml_dict[node_path] = {
            "staticUID": node_id
        }  # Convert ID to a 3-digit decimal string
    else:
        yaml_dict[node_path] = {
            "staticUID": f"0x{node_id}"
        }  # Convert ID to a 3-digit decimal string

    yaml_dict[node_path]["type"] = str(node.type.value)
    if node.unit:
        yaml_dict[node_path]["unit"] = str(node.unit.value)
    if node.is_signal() or node.is_property():
        yaml_dict[node_path]["datatype"] = node.data_type_str

    for child in node.children:
        id_counter, id_counter = export_node(
            yaml_dict, child, id_counter, offset, layer, no_layer, decimal_output
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
    )

    if config.validate_static_uid:
        logging.info(
            f"Now validating nodes, static UIDs, types, units and description with file '{config.validate_static_uid}'"
        )
        if os.path.isabs(config.validate_static_uid):
            other_path = config.validate_static_uid
        else:
            other_path = os.path.join(os.getcwd(), config.validate_static_uid)
        # ToDo: how do we know here if SIGNAL or DATA_TYPE tree
        validation_tree = load_tree(
            other_path, ["."], tree_type=VSSTreeType.SIGNAL_TREE
        )
        validate_staticUIDs(signals_yaml_dict, validation_tree, config)

    with open(config.output_file, "w") as f:
        yaml.dump(signals_yaml_dict, f)


def validate_staticUIDs(
    signals_dict: dict, validation_tree: VSSNode, config: argparse.Namespace
):
    """Check if static UIDs have changed or if new ones need to be added
    ToDos:
        - instances
        - automatic mode --> do we overwrite with a next higher ID because data in node has changed?

    Args:
        validation_tree (VSSNode): _description_
    Returns:
        Optional[dict]: _description_
    """
    highest_id: int = 0

    def check_length(key, value, decimal_output):
        """Check if static UID exists and if it's of correct length

        Args:
            key (str): Current key of the dict, evaluates to the qualified name of the node
            value (dict): dict of attributes e.g. static UID
        """
        if not value["staticUID"]:
            logging.error(f"Static UID for node '{key}' has not been assigned!")
        else:
            if decimal_output:
                try:
                    assert len(value["staticUID"]) == 8
                except AssertionError:
                    logging.error(
                        f"AssertionError: Length of hex static UID of {key} is incorrect, "
                        "did you check your command line arguments and if they match with "
                        "the validation file? There are multiple options e.g. "
                        "'--gen-no-layer' or '--gen-decimal-ID'."
                    )
            else:
                try:
                    if config.gen_no_layer:
                        assert len(value["staticUID"]) == 8
                    else:
                        assert len(value["staticUID"]) == 10
                except AssertionError:
                    logging.error(
                        f"AssertionError: Length of hex static UID of {key} is incorrect, "
                        "did you check your command line arguments and if they match with "
                        "the validation file? There are multiple options e.g. "
                        "'--gen-no-layer' or '--gen-decimal-ID'."
                    )

    def check_uid(k: str, v: dict, match_tuple: tuple):
        """Validates uid and either assigns next higher id or overwrites with validation id.
        If used in automatic mode it will always assign a new higher id for mismatches. In
        manual mode it will ask you what you would like to do.

        Args:
            k (str): current key in signals dict
            v (dict): current value contains another dict
            match_tuple (tuple): is the name and id of the matched names in validation tree
        """
        nonlocal highest_id

        try:
            validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]
            assert (
                value["staticUID"] == validation_node.extended_attributes["staticUID"]
            )

        except AssertionError:
            if config.validate_automatic_mode:
                assign_new_id(key, value)
            else:
                logging.info(
                    f"IDs don't match what would you like to do? Current tree's node '{key}' "
                    f"has static UID '{value['staticUID']} and other "
                    f"tree's node '{validation_tree_nodes[match_tuple[1]].qualified_name()}' "
                    f"has static UID "
                    f"'{validation_tree_nodes[match_tuple[1]].extended_attributes['staticUID']}'\n"
                    f"1) Assign new ID\n2) Overwrite ID with validation ID"
                )
                while True:
                    try:
                        overwrite_method = OverwriteMethod(int(input()))
                        if overwrite_method == OverwriteMethod.ASSIGN_NEW_ID:
                            assign_new_id(key, value)
                        elif (
                            overwrite_method
                            == OverwriteMethod.OVERWRITE_ID_WITH_VALIDATION_ID
                        ):
                            overwrite_current_id(
                                key,
                                value,
                                validation_tree_nodes[
                                    match_tuple[1]
                                ].extended_attributes["staticUID"],
                            )
                    except ValueError:
                        logging.info(
                            "Wrong input please choose again\n1) Assign new ID\n2) Overwrite ID with validation ID"
                        )
                        continue
                    else:
                        break

    def check_unit(k: str, v: dict, match_tuple: tuple):
        nonlocal config
        nonlocal highest_id

        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        if "unit" in v.keys() and validation_node.has_unit():
            try:
                assert v["unit"] == validation_node.unit
            except AssertionError:
                logging.info(
                    f"Units of '{key}' in unit: '{v['unit']}' in the current "
                    f"specification and the validation file '{key}' in unit: "
                    f"'{validation_node.unit}' don't match which causes a "
                    "breaking change, so we need to assign a new id!"
                )
                assign_new_id(k, v)

    def check_datatype(k: str, v: dict, match_tuple: tuple):
        nonlocal config
        nonlocal highest_id

        validation_node: VSSNode = validation_tree_nodes[match_tuple[1]]

        if "datatype" in v.keys() and validation_node.has_datatype():
            try:
                assert v["datatype"] == validation_node.get_datatype()
            except AssertionError:
                logging.info(
                    f"Types of '{key}' of datatype: '{v['datatype']}' in the current "
                    f"specification and the validation file '{key}' of datatype: "
                    f"'{validation_node.get_datatype()}' don't match which causes a "
                    "breaking change, so we need to assign a new id!"
                )
                assign_new_id(k, v)

    def check_names(k: str, v: dict, match_tuple: tuple):
        pass

    def assign_new_id(k: str, v: dict) -> None:
        """Assignment of next higher static UID if there is a mismatch of the current
        file and the validation file

        Args:
            k (str): current key of dict
            v (dict): current value of dict (also a dict)
            assign_id (int): the highest ID found in the original file
            config (argparse.Namespace): command line configuration from argparser
        """
        nonlocal config
        nonlocal highest_id

        highest_id += 1

        assign_static_uid: str
        if config.gen_decimal_ID:
            assign_static_uid = str(highest_id).zfill(6)
        else:
            if config.gen_no_layer:
                assign_static_uid = "0x" + format(highest_id, "06X")
            else:
                assign_static_uid = "0x" + format(
                    highest_id << 8 | config.gen_layer_ID_offset, "08X"
                )

        v["staticUID"] = assign_static_uid
        logging.info(f"Assigned new ID '{assign_static_uid}' for {k}")

    def overwrite_current_id(k: str, v: dict, current_id) -> None:
        """Overwrite method for the validation step of static UID assignment

        Args:
            k (str): current key of dict
            v (dict): current value of dict (also a dict)
            current_id (_type_): the id that you want to overwrite the old ID with
        """
        v["staticUID"] = current_id
        logging.info(f"Assigned new ID '{current_id}' for {k}")

    def get_id_from_string(hex_string: str) -> int:
        nonlocal config
        curr_value: int
        if not config.gen_no_layer and not config.gen_decimal_ID:
            curr_value = int(hex_string, 16) - config.gen_ID_offset
            curr_value = (curr_value ^ config.gen_layer_ID_offset) >> 8
        else:
            curr_value = int(hex_string, 16)
        return curr_value

    # go to top in case we are not
    if validation_tree.parent:
        while validation_tree.parent:
            validation_tree = validation_tree.parent

    # need current highest id new assignments during validation
    for key, value in signals_dict.items():
        current_id: int = get_id_from_string(value["staticUID"])
        if current_id > highest_id:
            highest_id = current_id

    validation_tree_nodes: list = []
    for node in PreOrderIter(validation_tree):
        validation_tree_nodes.append(node)
        current_id_val: int = get_id_from_string(node.extended_attributes["staticUID"])
        if current_id_val > highest_id:
            highest_id = current_id_val

    # check if all nodes have staticUID of correct length
    for key, value in signals_dict.items():
        check_length(key, value, decimal_output=config.gen_decimal_ID)

        # ToDo: what if there was no match? we need optional method?
        matched_names = [
            (key, id_validation_tree)
            for id_validation_tree, other_node in enumerate(validation_tree_nodes)
            if key == other_node.qualified_name()
        ]
        if len(matched_names) > 1:
            logging.warning(
                "Caution there were multiple matches with same names. Please check "
                "your vspec specification or validation file for duplicates!"
            )
        for match in matched_names:
            # check for static uid changes using matched
            check_uid(key, value, match)
            check_unit(key, value, match)
            check_datatype(key, value, match)

        matched_uids = [
            (key, id_validation_tree)
            for id_validation_tree, other_node in enumerate(validation_tree_nodes)
            if value["staticUID"] == other_node.extended_attributes["staticUID"]
        ]
        for match in matched_uids:
            check_names(key, value, match)

    # ToDo same loop as above but match static UIDs and check for name changes


if __name__ == "__main__":
    initLogging()
