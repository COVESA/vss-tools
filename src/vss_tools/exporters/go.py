# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0


from __future__ import annotations

import re
from pathlib import Path

import rich_click as click
from anytree import PreOrderIter

import vss_tools.cli_options as clo
from vss_tools import log
from vss_tools.datatypes import Datatypes, is_array
from vss_tools.main import get_trees
from vss_tools.model import VSSDataBranch, VSSDataDatatype, VSSDataStruct
from vss_tools.tree import VSSNode

datatype_map = {
    Datatypes.INT8_ARRAY[0]: "[]int8",
    Datatypes.INT16_ARRAY[0]: "[]int16",
    Datatypes.INT32_ARRAY[0]: "[]int32",
    Datatypes.INT64_ARRAY[0]: "[]int64",
    Datatypes.UINT8_ARRAY[0]: "[]uint8",
    Datatypes.UINT16_ARRAY[0]: "[]uint16",
    Datatypes.UINT32_ARRAY[0]: "[]uint32",
    Datatypes.UINT64_ARRAY[0]: "[]uint64",
    Datatypes.FLOAT[0]: "float32",
    Datatypes.FLOAT_ARRAY[0]: "[]float32",
    Datatypes.DOUBLE[0]: "float64",
    Datatypes.DOUBLE_ARRAY[0]: "[]float64",
    Datatypes.STRING_ARRAY[0]: "[]string",
    Datatypes.NUMERIC[0]: "float64",
    Datatypes.NUMERIC_ARRAY[0]: "[]float64",
    Datatypes.BOOLEAN_ARRAY[0]: "[]bool",
    Datatypes.BOOLEAN[0]: "bool",
}


def add_children_map_entries(root: VSSNode, fqn: str, replace: str, map: dict[str, str]) -> None:
    """
    Adding rename map entries for children of a given node
    """
    child: VSSNode
    for child in root.children:
        child_fqn = child.get_fqn()
        new_name = child_fqn.replace(fqn, replace)
        map[child_fqn] = new_name
        add_children_map_entries(child, fqn, replace, map)


def get_instance_mapping(root: VSSNode | None) -> dict[str, str]:
    """
    Constructing a rename map of fqn->new_name.
    The last instance of the node will have the concept name of the node (e.g. Door)
    All intances of it will be named <concept>.I<N> ("I" for instance)

    E.g. "Vehicle.Cabin.Door.Row1.DriverSide.Window"
    will result in pseudo code types:

    Cabin
        Door DoorI2

    DoorR2
        Row1 DoorI1
        Row2 DoorI1

    DoorR1
        DriverSide Door
        PassengerSide Door
    """

    if root is None:
        return {}
    instance_map: dict[str, str] = {}
    for node in PreOrderIter(root):
        if isinstance(node.data, VSSDataBranch):
            instance_children_depth = node.count_instance_children_depth()

            if instance_children_depth == 0:
                if not node.data.is_instance:
                    continue

            instance_root, _ = node.get_instance_root()
            fqn = node.get_fqn()

            if instance_children_depth > 0:
                instance_map[fqn] = f"{instance_root.get_fqn()}.I{instance_children_depth}"
            else:
                instance_map[fqn] = instance_root.get_fqn()
            add_children_map_entries(node, fqn, instance_map[fqn], instance_map)

    return instance_map


def get_datatype(node: VSSNode) -> str | None:
    """
    Gets the datatype string of a node.
    """
    datatype = None
    if isinstance(node.data, VSSDataDatatype):
        if node.data.datatype in datatype_map:
            return datatype_map[node.data.datatype]
        d = Datatypes.get_type(node.data.datatype)
        if d:
            datatype = d[0]
        # Struct type
        d_raw = node.data.datatype
        array = is_array(d_raw)
        struct_datatype = node.data.datatype.rstrip("[]")
        if array:
            struct_datatype = f"[]{struct_datatype}"
        datatype = struct_datatype
    return datatype


class GoStructMember:
    def __init__(self, name: str, datatype: str) -> None:
        self.name = name
        self.datatype = datatype


class GoStruct:
    def __init__(self, name: str) -> None:
        self.name = name
        self.members: list[GoStructMember] = []

    def __str__(self) -> str:
        r = f"type {self.name.replace('.', '')} struct {{\n"
        for member in self.members:
            r += f"\t{member.name} {member.datatype.replace('.', '')}\n"
        r += "}\n"
        return r

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GoStruct):
            return False
        return self.name == other.name


def get_struct_name(fqn: str, map: dict[str, str]) -> str:
    if fqn in map:
        return map[fqn]
    else:
        return fqn


def get_go_structs(root: VSSNode | None, map: dict[str, str], type_tree: bool = False) -> dict[str, GoStruct]:
    structs: dict[str, GoStruct] = {}
    if root is None:
        return structs
    for node in PreOrderIter(root):
        if isinstance(node.data, VSSDataBranch) or isinstance(node.data, VSSDataStruct):
            struct = GoStruct(get_struct_name(node.get_fqn(), map))
            for child in node.children:
                datatype = get_datatype(child)
                if not datatype:
                    datatype = get_struct_name(child.get_fqn(), map)
                member = GoStructMember(child.name, datatype)
                struct.members.append(member)
            if type_tree and isinstance(node.data, VSSDataBranch):
                pass
            else:
                structs[struct.name] = struct
    return structs


def get_prefixes(structs: dict[str, GoStruct]) -> list[str]:
    """
    Gets all current prefixes from the given structs.
    Example:

    Vehicle.Cabin
    Something.Else

    -> [Vehicle, Something]
    """
    prefixes: dict[str, int] = {}
    for struct in structs.values():
        split = struct.name.split(".")
        if len(split) == 1:
            continue
        prefix = split[0]
        if prefix in prefixes:
            prefixes[prefix] += 1
        else:
            prefixes[prefix] = 1
    return [p for p in prefixes.keys()]


def get_prefix_strip_conflicts(prefix: str, structs: dict[str, GoStruct]) -> int:
    """
    Finds conflicts if we would strip the given prefix from structs
    """
    structs_new: list[str] = []
    for struct in structs.values():
        split = struct.name.split(".")
        sp = split[0]
        if len(split) == 1:
            structs_new.append(struct.name)
        else:
            if sp != prefix:
                structs_new.append(struct.name)
            else:
                log.debug(f"Stripping, {prefix=}, {struct.name=}")
                structs_new.append(".".join(split[1:]))
                log.debug(f"New name: {structs_new[-1]}")

    return len(structs_new) - len(set(structs_new))


def is_only_instance(s: str) -> bool:
    """
    Whether a string is only an instance ID.
    We do not want to end up in struct names only having "I1" or "I2"
    """
    pattern = r"^I\d+$"
    match = re.match(pattern, s)
    if match:
        return True
    return False


def strip_structs_prefix(prefix: str, structs: dict[str, GoStruct]) -> int:
    """
    Left strips all structs from the given prefix
    Returns the number of changed struct names
    """
    stripped = 0
    for struct in structs.values():
        split = struct.name.split(".")
        if len(split) > 1:
            if split[0] == prefix:
                new_name = ".".join(split[1:])
                if is_only_instance(new_name):
                    log.debug(f"Struct, not stripping, would be Instance id only: {struct.name}")
                else:
                    struct.name = new_name
                    stripped += 1
        for member in struct.members:
            dtsplit = member.datatype.split(".")
            if len(dtsplit) > 1:
                array_member = dtsplit[0].startswith("[]")
                content = dtsplit[0].lstrip("[]")
                if content == prefix:
                    new_name = ".".join(dtsplit[1:])
                    if is_only_instance(new_name):
                        log.debug(f"Member, not stripping, would be Instance id only: {member.datatype}")
                    else:
                        member.datatype = new_name
                        if array_member:
                            member.datatype = "[]" + member.datatype
    return stripped


@click.command()
@clo.vspec_opt
@clo.output_required_opt
@clo.include_dirs_opt
@clo.extended_attributes_opt
@clo.strict_opt
@clo.aborts_opt
@clo.overlays_opt
@clo.quantities_opt
@clo.units_opt
@clo.types_opt
@clo.strict_exceptions_opt
@click.option("--package", default="vss", help="Go package name", show_default=True)
@click.option("--short-names/--no-short-names", default=True, show_default=True, help="Shorten struct names")
def cli(
    vspec: Path,
    output: Path,
    include_dirs: tuple[Path],
    extended_attributes: tuple[str],
    strict: bool,
    aborts: tuple[str],
    overlays: tuple[Path],
    quantities: tuple[Path],
    units: tuple[Path],
    types: tuple[Path],
    package: str,
    short_names: bool,
    strict_exceptions: Path | None,
):
    """
    Export as Go structs.
    """
    tree, datatype_tree = get_trees(
        vspec=vspec,
        include_dirs=include_dirs,
        aborts=aborts,
        strict=strict,
        extended_attributes=extended_attributes,
        quantities=quantities,
        units=units,
        types=types,
        overlays=overlays,
        strict_exceptions_file=strict_exceptions,
    )
    instance_map = get_instance_mapping(tree)
    structs = get_go_structs(tree, instance_map)
    log.info(f"Structs, amount={len(structs)}")
    datatype_structs = get_go_structs(datatype_tree, instance_map, True)
    log.info(f"Datatype structs, amount={len(datatype_structs)}")
    structs.update(datatype_structs)

    if short_names:
        rounds = 0
        while True:
            prefixes = get_prefixes(structs)
            log.debug(f"{prefixes=}")
            stripped = 0
            for prefix in prefixes:
                conflicts = get_prefix_strip_conflicts(prefix, structs)
                log.debug(f"Struct name conflicts, prefix={prefix}, conflicts={conflicts}")
                if conflicts == 0:
                    stripped += strip_structs_prefix(prefix, structs)
                    log.info(f"Stripping '{prefix}', round={rounds}, {stripped=}")
            if stripped == 0:
                break
            else:
                rounds += 1

    with open(output, "w") as f:
        f.write(f"package {package}\n\n")
        for struct in structs.values():
            f.write(str(struct))
