# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0


def get_node_identifier_bytes(
    qualified_name: str,
    data_type: str,
    node_type: str,
    unit: str,
    allowed: str,
    minimum: str,
    maximum: str,
    strict_mode: bool,
) -> bytes:
    """Get a node identifier as bytes. Used as an input for hashing

    @param qualified_name: full path to the node
    @param data_type: its datatype
    @param node_type: its node type
    @param unit: the unit if it uses one
    @param allowed: the enum for allowed values
    @param minimum: min value for the data if exists
    @param maximum: max value for the data if exists
    @param strict_mode: strict mode means case sensitivity of node qualified names
    @return: a bytes representation of the node
    """

    node_identifier: bytes = (
        f"{qualified_name}: "
        f"unit: {unit}, "
        f"datatype: {data_type}, "
        f"type: {node_type}"
        f"allowed: {allowed}"
        f"min: {minimum}"
        f"max: {maximum}"
    ).encode()

    if strict_mode:
        return node_identifier
    else:
        return node_identifier.lower()


def fnv1_32_hash(identifier: bytes) -> int:
    """32-bit hash of a node according to Fowler–Noll–Vo

    @param identifier: a bytes representation of a node
    @return: hashed value for the node as int
    """
    id_hash = 2166136261
    for byte in identifier:
        id_hash = (id_hash * 16777619) & 0xFFFFFFFF
        id_hash ^= byte

    return id_hash


def fnv1_32_wrapper(name: str, source: dict, strict_mode: bool):
    """A wrapper for the 32-bit hashing function if the input node
     is represented as dict instead of VSSNode

    @param name: full name aka qualified name
    @param source:
    @param strict_mode: strict mode means case sensitivity of node qualified names
    @return:
    """
    # Verify and assign values from source dictionary using source.get
    allowed: str = source.get("allowed", "")
    minimum: str = source.get("min", "")
    maximum: str = source.get("max", "")
    datatype: str = source.get("datatype", "")
    vsstype: str = source.get("type", "")
    unit: str = source.get("unit", "")

    identifier = get_node_identifier_bytes(
        name,
        datatype,
        vsstype,
        unit,
        allowed,
        minimum,
        maximum,
        strict_mode,
    )
    return format(fnv1_32_hash(identifier), "08X")


def get_all_keys_values(d: dict):
    for key, value in d.items():
        yield key, value
        if isinstance(value, dict):
            yield from get_all_keys_values(value)
