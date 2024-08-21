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

import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import rich_click as click
import yaml

import vss_tools.vspec.cli_options as clo
from vss_tools import log
from vss_tools.vspec.main import get_trees
from vss_tools.vspec.tree import VSSNode
from vss_tools.vspec.utils import vss2id_val
from vss_tools.vspec.utils.idgen_utils import (
    fnv1_32_hash,
    get_all_keys_values,
    get_node_identifier_bytes,
)
from vss_tools.vspec.utils.misc import getattr_nn


def generate_split_id(node: VSSNode, id_counter: int, strict_mode: bool) -> Tuple[str, int]:
    """Generates static UIDs using 4-byte FNV-1 hash.

    @param node: VSSNode that we want to generate a static UID for
    @param id_counter: consecutive numbers counter for amount of nodes
    @param strict_mode: strict mode means case sensitivity for static UID generation
    @return: tuple of hashed string and id counter
    """

    fka = getattr(node.data, "fka", None)
    if fka:
        name = fka[0] if isinstance(fka, list) else fka
    else:
        name = node.get_fqn()
    data = node.get_vss_data()
    datatype = getattr_nn(data, "datatype", "")
    unit = getattr_nn(data, "unit", "")
    allowed = getattr_nn(data, "allowed", "")
    if allowed == []:
        allowed = ""
    min = getattr_nn(data, "min", "")
    max = getattr_nn(data, "max", "")
    identifier = get_node_identifier_bytes(
        name,
        datatype,
        data.type.value,
        unit,
        allowed,
        min,
        max,
        strict_mode,
    )
    hashed_str = format(fnv1_32_hash(identifier), "08X")

    return hashed_str, id_counter + 1


def export_node(data: dict[str, Any], node: VSSNode, id_counter, strict_mode: bool) -> Tuple[int, int]:
    """Recursive function to export the full tree to a dict

    @param data: the to be exported dict
    @param node: parent node of the tree
    @param id_counter: counter for amount of ids
    @param strict_mode: strict mode means case sensitivity for static UID generation
    @return: id_counter, id_counter
    """

    node_id: str
    node_data = node.get_vss_data()
    if node_data.constUID:
        log.info(
            f"Using const ID for {node.get_fqn()}. If you didn't mean "
            "to do that you can remove it in your vspec / overlay."
        )
        node_id = node_data.constUID
    else:
        node_id, id_counter = generate_split_id(node, id_counter, strict_mode)
        node_id = f"0x{node_id}"

    # check for hash duplicates
    for key, value in get_all_keys_values(data):
        if not isinstance(value, dict) and key == "staticUID":
            if node_id == value:
                log.fatal(
                    f"There is a small chance that the result of FNV-1 "
                    f"hashes are the same in this case the hash of node "
                    f"'{node.get_fqn()}' is the same as another hash."
                    f"Can you please update it."
                )
                # We could add handling of duplicates here
                sys.exit(-1)

    node_path = node.get_fqn()

    data[node_path] = {"staticUID": f"{node_id}"}
    data[node_path]["description"] = node_data.description
    data[node_path]["type"] = str(node_data.type.value)
    if getattr(node_data, "unit", None):
        data[node_path]["unit"] = getattr(node_data, "unit")
    if hasattr(node_data, "datatype"):
        data[node_path]["datatype"] = getattr(node_data, "datatype")
    if getattr(node_data, "allowed", None):
        data[node_path]["allowed"] = getattr(node_data, "allowed")

    min = getattr(node_data, "min", None)
    if min is not None:
        data[node_path]["min"] = min
    max = getattr(node_data, "max", None)
    if max is not None:
        data[node_path]["max"] = max

    fka = getattr(node_data, "fka", None)
    if fka:
        data[node_path]["fka"] = fka

    if node_data.deprecation:
        data[node_path]["deprecation"] = node_data.deprecation

    for child in node.children:
        id_counter, id_counter = export_node(data, child, id_counter, strict_mode)

    return id_counter, id_counter


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.uuid_opt
@clo.expand_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@click.option(
    "--validate-static-uid",
    type=click.Path(dir_okay=False, readable=True, exists=True, path_type=Path),
    help="Validation file.",
)
@click.option("--validate-only", is_flag=True, help="Only validating. Not exporting.")
@click.option(
    "--case-sensitive",
    is_flag=True,
    help="Whether the generation of static UIDs is case-sensitive",
)
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    uuid: bool,
    expand: bool,
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    validate_static_uid: Path,
    validate_only: bool,
    case_sensitive: bool,
):
    """
    Export as IDs.
    """
    tree, _ = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        uuid=uuid,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        expand=expand,
    )
    log.info("Generating vspec output including static UIDs...")

    id_counter: int = 0
    signals_yaml_dict: Dict[str, str] = {}  # Use str for ID values
    id_counter, _ = export_node(signals_yaml_dict, tree, id_counter, case_sensitive)

    if validate_static_uid:
        log.info(
            f"Now validating nodes, static UIDs, types, units and description with " f"file '{validate_static_uid}'"
        )

        validation_tree, _ = get_trees(
            vspec=validate_static_uid,
            include_dirs=include_dirs,
            aborts=aborts,
            strict=strict,
            extended_attributes=extended_attributes,
            uuid=uuid,
            quantities=quantities,
            units=units,
            types=types,
            expand=expand,
        )
        vss2id_val.validate_static_uids(signals_yaml_dict, validation_tree, strict)

    if not validate_only:
        with open(output, "w") as f:
            yaml.dump(signals_yaml_dict, f)
