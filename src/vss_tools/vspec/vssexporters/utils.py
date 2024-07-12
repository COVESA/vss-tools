# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from vss_tools import log
from vss_tools.vspec import (
    load_quantities,
    load_units,
    verify_mandatory_attributes,
    load_tree,
    merge_tree,
    check_type_usage,
    expand_tree_instances,
    clean_metadata,
)
from vss_tools.vspec import VSSNode, VSSTreeType, VSpecError
from pathlib import Path
import sys


class ArgumentException(Exception):
    pass


def get_trees(
    include_dirs: tuple[Path],
    aborts: tuple[str],
    strict: bool,
    extended_attributes: tuple[str],
    uuid: bool,
    quantities: tuple[Path],
    vspec: Path,
    units: tuple[Path],
    types: tuple[Path, ...],
    types_output: Path | None,
    overlays: tuple[Path],
    expand: bool,
) -> tuple[VSSNode, VSSNode | None]:
    includes = list(include_dirs)
    includes.extend([Path.cwd(), vspec.parent])

    abort_on_unknown_attribute = False
    abort_on_namestyle = False

    if "unknown-attributes" in aborts or strict:
        abort_on_unknown_attribute = True
    if "name-style" in aborts or strict:
        abort_on_namestyle = True

    if extended_attributes:
        VSSNode.whitelisted_extended_attributes = list(extended_attributes)
        log.info(f"Known extended attributes: {', '.join(extended_attributes)}")
    else:
        extended_attributes = list()

    # Follow up to https://github.com/COVESA/vehicle_signal_specification/pull/721
    # Deprecate --uuid
    if uuid:
        log.warning(
            "The argument --uuid is deprecated and the uuid feature is planned"
            "to be removed in VSS-tools 6.0"
        )
        log.info("If you need static identifiers consider using the vspec2id tool")

    qs = [str(q) for q in quantities]
    load_quantities(str(vspec), qs)
    us = [str(u) for u in units]
    load_units(str(vspec), us)

    # process data type tree
    data_type_tree = None
    if types_output:
        if types_output and not types:
            raise ArgumentException(
                "An output file for data types was provided. Please also provide "
                "the input vspec file for data types"
            )
    if types:
        data_type_tree = processDataTypeTree(
            types_output, types, includes, abort_on_namestyle
        )
        verify_mandatory_attributes(data_type_tree, abort_on_unknown_attribute)

    try:
        log.info(f"Loading vspec from {vspec}...")
        tree = load_tree(
            str(vspec),
            includes,
            VSSTreeType.SIGNAL_TREE,
            break_on_name_style_violation=abort_on_namestyle,
            expand_inst=False,
            data_type_tree=data_type_tree,
        )

        VSSNode.set_reference_tree(tree)

        for overlay in overlays:
            log.info(f"Applying VSS overlay from {overlay}...")
            othertree = load_tree(
                str(overlay),
                includes,
                VSSTreeType.SIGNAL_TREE,
                break_on_name_style_violation=abort_on_namestyle,
                expand_inst=False,
                data_type_tree=data_type_tree,
            )
            merge_tree(tree, othertree)

        check_type_usage(tree, VSSTreeType.SIGNAL_TREE, data_type_tree)
        if expand:
            expand_tree_instances(tree)

        clean_metadata(tree)
        verify_mandatory_attributes(tree, abort_on_unknown_attribute)
        return tree, data_type_tree

    except VSpecError as e:
        log.error(f"Error: {e}")
        sys.exit(255)


def processDataTypeTree(
    types_output: Path | None,
    types: tuple[Path, ...],
    include_dir: list[Path],
    abort_on_namestyle: bool,
) -> VSSNode:
    """
    Helper function to process command line arguments and invoke logic for processing data
    type information provided in vspec format
    """
    if types_output:
        log.info("Sensors and custom data types will be consolidated into one file.")

    first_tree = True
    for type_file in types:
        log.info(f"Loading and processing struct/data type tree from {type_file}")
        new_tree = load_tree(
            str(type_file),
            include_dir,
            VSSTreeType.DATA_TYPE_TREE,
            break_on_name_style_violation=abort_on_namestyle,
            expand_inst=False,
        )
        if first_tree:
            tree = new_tree
            first_tree = False
        else:
            merge_tree(tree, new_tree)
    check_type_usage(tree, VSSTreeType.DATA_TYPE_TREE)
    return tree
