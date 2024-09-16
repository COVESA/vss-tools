# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

from anytree import PreOrderIter, findall

from vss_tools import log
from vss_tools.vspec.datatypes import (
    dynamic_datatypes,
    dynamic_quantities,
    dynamic_units,
)
from vss_tools.vspec.model import (
    VSSDataBranch,
    VSSDataProperty,
    VSSDataStruct,
    get_all_model_fields,
)
from vss_tools.vspec.tree import ModelValidationException, VSSNode, build_tree
from vss_tools.vspec.units_quantities import load_quantities, load_units
from vss_tools.vspec.vspec import InvalidSpecDuplicatedEntryException, load_vspec


class NameViolationException(Exception):
    pass


class ExtraAttributesException(Exception):
    pass


class MultipleTypeTreesException(Exception):
    pass


class RootTypesException(Exception):
    pass


class PropertyOrphansException(Exception):
    pass


def load_quantities_and_units(quantities: tuple[Path, ...], units: tuple[Path, ...], vspec_root: Path) -> None:
    """
    Loading quantities and units.
    Side effect: filling global 'dynamic_quantities' and 'dynamic_units' from 'datatypes'
    """
    if not quantities:
        default_quantity = vspec_root / "quantities.yaml"
        if default_quantity.exists():
            quantities = (default_quantity,)
        else:
            log.warning(f"No 'quantity' files defined. Default not existing: {default_quantity.absolute()}")
    if not units:
        default_unit = vspec_root / "units.yaml"
        if default_unit.exists():
            units = (default_unit,)
        else:
            log.warning(f"No 'unit' files defined. Default not existing: {default_unit.absolute()}")

    quantity_data = load_quantities(list(quantities))
    dynamic_quantities.extend(list(quantity_data.keys()))
    unit_data = load_units(list(units))
    for k, v in unit_data.items():
        allowed_datatypes = []
        if v.allowed_datatypes is not None:
            allowed_datatypes = v.allowed_datatypes
        if v.unit is not None:
            dynamic_units[v.unit] = allowed_datatypes
        dynamic_units[k] = allowed_datatypes


def check_name_violations(root: VSSNode, strict: bool, aborts: tuple[str, ...]) -> None:
    if strict or "name-style" in aborts:
        naming_violations = root.get_naming_violations()
        if naming_violations:
            for violation in naming_violations:
                log.warning(f"Name violation: '{violation[0]}' ({violation[1]})")
            raise NameViolationException(f"Name violations detected: {naming_violations}")


def check_extra_attribute_violations(
    root: VSSNode,
    strict: bool,
    aborts: tuple[str, ...],
    extended_attributes: tuple[str, ...],
) -> None:
    extra_attributes = root.get_extra_attributes(extended_attributes)
    for attribute in extra_attributes:
        log.warning(f"Unknown extra attribute: '{attribute[0]}':'{attribute[1]}'")
        if attribute[1] in get_all_model_fields():
            raise ExtraAttributesException(
                f"Forbidden extra attribute (core attribute): '{attribute[0]}':'{attribute[1]}'"
            )
    if strict or "unknown-attribute" in aborts:
        if extra_attributes:
            raise ExtraAttributesException(f"Forbidden extra attributes detected: {extra_attributes}")


def get_types_root(types: tuple[Path, ...], include_dirs: list[Path]) -> VSSNode | None:
    if not types:
        log.debug("No user 'types' defined")
        return None

    types_root: VSSNode | None = None
    # We are iterating to be able to reference
    # types from earlier type files
    for types_file in list(types):
        data = load_vspec(include_dirs, [types_file], "Types")
        root, orphans = build_tree(data.data)
        if orphans:
            log.error(f"Types model has orphans\n{orphans}")
            exit(1)
        if types_root:
            node: VSSNode
            for node in PreOrderIter(root):
                if not types_root.connect(node.get_fqn(), node):
                    raise MultipleTypeTreesException()
        else:
            types_root = root

    if dynamic_datatypes:
        log.info(f"Dynamic datatypes added={len(dynamic_datatypes)}")
        log.debug(f"Dynamic datatypes:\n{dynamic_datatypes}")

    # Checking whether user defined root types e.g 'MyType'
    # instead of 'Types.MyType'
    if not all(["." in t for t in dynamic_datatypes]):
        raise RootTypesException()

    if types_root:
        try:
            types_root.resolve()
        except ModelValidationException as e:
            log.critical(e)
            exit(1)

    return types_root


def get_invalid_node_msgs(root: VSSNode) -> list[str]:
    """
    Validating whether tree nodes have correct parents
    All nodes need 'branch' parents except 'properties'.
    Properties need a 'struct' as a parent.
    Returning error msgs
    """
    invalid_nodes = []
    for node in PreOrderIter(root):
        ok = True
        if node.parent is None:
            continue
        if isinstance(node.data, VSSDataProperty):
            if not isinstance(node.parent.data, VSSDataStruct):
                ok = False
        elif isinstance(node.data, VSSDataStruct):
            if not isinstance(node.parent.data, VSSDataStruct) and not isinstance(node.parent.data, VSSDataBranch):
                ok = False
        else:
            if not isinstance(node.parent.data, VSSDataBranch):
                ok = False
        if not ok:
            entry = f"'{node.get_fqn()} ({node.data.__class__.__name__})',"
            entry += f" invalid parent: '{node.parent.data.__class__.__name__}'"
            invalid_nodes.append(entry)
    return invalid_nodes


def validate_tree(root: VSSNode) -> None:
    invalid_node_msgs = get_invalid_node_msgs(root)
    if invalid_node_msgs:
        log.critical(f"Invalid nodes={len(invalid_node_msgs)}")
        for node in invalid_node_msgs:
            log.critical(node)
        exit(1)


def get_trees(
    vspec: Path,
    include_dirs: tuple[Path, ...] = (),
    aborts: tuple[str, ...] = (),
    strict: bool = False,
    extended_attributes: tuple[str, ...] = (),
    uuid: bool = False,
    quantities: tuple[Path, ...] = (),
    units: tuple[Path, ...] = (),
    types: tuple[Path, ...] = (),
    overlays: tuple[Path, ...] = (),
    expand: bool = True,
) -> tuple[VSSNode, VSSNode | None]:
    """
    Loading vspec files, building and validating trees (types and normal).
    Returning a tuple of the root and the types tree
    """
    if extended_attributes:
        log.info(f"User defined extra attributes: {extended_attributes}")
    try:
        load_quantities_and_units(quantities, units, vspec.parent)
    except ModelValidationException as e:
        log.critical(e)
        exit(1)

    unique_include_dirs = []
    for include_dir in include_dirs:
        if include_dir not in unique_include_dirs:
            unique_include_dirs.append(include_dir)

    try:
        types_root = get_types_root(types, unique_include_dirs)
        vspec_data = load_vspec(unique_include_dirs, [vspec] + list(overlays))
    except InvalidSpecDuplicatedEntryException as e:
        log.critical(e)
        exit(1)

    root, orphans = build_tree(vspec_data.data, connect_orphans=True)

    if orphans:
        log.error(f"Model has orphans\n{list(orphans.keys())}")
        exit(1)

    if expand:
        root.expand_instances()

    if uuid:
        log.warning("UUID support is deprecated and will be removed in VSS-tools 6.0")
        root.add_uuids()

    try:
        root.resolve()
    except ModelValidationException as e:
        log.critical(e)
        exit(1)

    root.delete_nodes(findall(root, filter_=lambda n: n.get_vss_data().delete))

    validate_tree(root)

    if types_root:
        validate_tree(types_root)
        try:
            check_extra_attribute_violations(types_root, True, aborts, extended_attributes)
        except (NameViolationException, ExtraAttributesException) as e:
            log.critical(e)
            exit(1)

    try:
        check_name_violations(root, strict, aborts)
        check_extra_attribute_violations(root, strict, aborts, extended_attributes)
    except (NameViolationException, ExtraAttributesException) as e:
        log.critical(e)
        exit(1)

    return root, types_root
