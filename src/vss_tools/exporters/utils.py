# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from anytree import PreOrderIter

from vss_tools.model import VSSDataBranch, VSSDataDatatype
from vss_tools.tree import VSSNode


class NoInstanceRootException(Exception):
    pass


def get_instance_root(root: VSSNode, depth: int = 1) -> tuple[VSSNode, int]:
    """
    Getting the root node of a given instance node.
    Going the tree upwards
    """
    if root.parent is None:
        raise NoInstanceRootException()
    if isinstance(root.parent.data, VSSDataBranch):
        if root.parent.data.is_instance:  # Is the inmmediate parent node also a VSS instance branch?
            return get_instance_root(root.parent, depth + 1)
        else:
            return root.parent, depth
    else:
        raise NoInstanceRootException()


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
    The new name has instances stripped and appending "I<N>" instead
    where N is the depth of the instance
    """
    if root is None:
        return {}
    instance_map: dict[str, str] = {}
    for node in PreOrderIter(root):
        if isinstance(node.data, VSSDataBranch):
            if node.data.is_instance:
                instance_root, depth = get_instance_root(node)
                new_name = instance_root.get_fqn() + "." + "I" + str(depth)
                fqn = node.get_fqn()
                instance_map[fqn] = new_name
                add_children_map_entries(node, fqn, instance_root.get_fqn(), instance_map)
    return instance_map


def get_instances_meta(root: VSSNode) -> dict[str, list[str]]:
    """
    Constructing metadata of instance root nodes fqns and a list of generated nodes
    """
    meta: dict[str, list[str]] = {}
    for node in PreOrderIter(root, filter_=lambda n: isinstance(n.data, VSSDataBranch) and n.data.is_instance):
        if any(c.data.is_instance for c in node.children if isinstance(c.data, VSSDataBranch)):
            continue
        instance_root, _ = get_instance_root(node)
        instance_root_fqn = instance_root.get_fqn()

        instance_name = node.get_fqn().removeprefix(instance_root_fqn + ".")

        if instance_root_fqn in meta:
            meta[instance_root_fqn].append(instance_name)
        else:
            meta[instance_root_fqn] = [instance_name]
    return meta


def is_VSS_leaf(node: VSSNode) -> bool:
    """Check if the node is a VSS leaf (i.e., one of VSS sensor, attribute, or actuator)"""
    if isinstance(node.data, VSSDataDatatype):
        return True
    return False


def is_VSS_branch(node: VSSNode) -> bool:
    """Check if the node is a VSS branch (and not an instance branch)"""
    if isinstance(node.data, VSSDataBranch):
        if not node.data.is_instance:
            return True
    return False


def is_VSS_branch_instance(node: VSSNode) -> bool:
    """Check if the node is a VSS branch instance)"""
    if isinstance(node.data, VSSDataBranch):
        if node.data.is_instance:
            return True
    return False
