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


def get_instances_meta(root: VSSNode) -> dict[str, list[str]]:
    """
    Constructing metadata of instance root nodes fqns and a list of generated nodes
    """
    meta: dict[str, list[str]] = {}
    for node in PreOrderIter(root, filter_=lambda n: isinstance(n.data, VSSDataBranch) and n.data.is_instance):
        if any(c.data.is_instance for c in node.children if isinstance(c.data, VSSDataBranch)):
            continue
        instance_root, _ = node.get_instance_root()
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
