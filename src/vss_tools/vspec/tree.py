# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import re
import uuid
from copy import deepcopy
from typing import Any

from anytree import Node, PreOrderIter, find, findall
from pydantic import ValidationError

from vss_tools import log
from vss_tools.vspec.datatypes import Datatypes, dynamic_datatypes
from vss_tools.vspec.model import (
    ModelValidationException,
    VSSData,
    VSSDataBranch,
    VSSDataDatatype,
    VSSDataStruct,
    VSSRaw,
    get_vss_raw,
    resolve_vss_raw,
)
from vss_tools.vspec.vspec import deep_update

SEPARATOR = "."


class NotMergeableException(Exception):
    pass


class NoRootsException(Exception):
    pass


class MultipleRootsException(Exception):
    pass


class InvalidExpansionEntryException(Exception):
    pass


class NoVSSDataException(Exception):
    pass


class VSSNode(Node):  # type: ignore[misc]
    """
    Our Anytree node class
    It contains the actual node data in the `data` attribute
    """

    separator = SEPARATOR

    def __init__(self, name: str, fqn: str | None, data: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(name, **kwargs)
        self.data = get_vss_raw(data, fqn)
        self.uuid: str | None = None

    def copy(self) -> VSSNode:
        node = VSSNode(
            self.name,
            self.get_fqn(),
            self.data.model_dump(
                mode="json",
                exclude=set(["fqn"]),
            ),
        )
        for c in self.children:
            cp = c.copy()
            cp.parent = node

        return node

    def _post_attach(self, parent: VSSNode):
        """
        Updating the data fqn when getting reattached.
        We need the fqn in the data for validation purposes.
        """
        log.debug(f"Got attached to parent='{parent.get_fqn()}', new fqn='{self.get_fqn()}'")
        self.data.fqn = self.get_fqn(SEPARATOR)

    def _post_detach(self, parent: VSSNode):
        log.debug(f"'{self.get_fqn()}', detached from parent='{parent.get_fqn()}'")

    def get_vss_data(self) -> VSSData:
        if not isinstance(self.data, VSSData):
            raise NoVSSDataException(f"'{self.get_fqn()}' data does not contain 'VSSData'")
        else:
            return self.data

    def get_fqn(self, sep: str = SEPARATOR) -> str:
        return sep.join([n.name for n in self.path])

    def resolve(self) -> None:
        """
        Resolves raw nodes into "higher" nodes
        """
        vss_raw_nodes = findall(self, filter_=lambda node: isinstance(node.data, VSSRaw))
        for node in vss_raw_nodes:
            try:
                node.data = resolve_vss_raw(node.data)
            except ValidationError as e:
                raise ModelValidationException(node.get_fqn(), e) from None

    def get_child(self, fqn: str) -> VSSNode | None:
        for child in self.children:
            if child.get_fqn() == fqn:
                log.debug(f"{self.get_fqn()}, found child='{child.get_fqn()}'")
                return child
        return None

    def merge(self, other: VSSNode) -> None:
        """
        Merges this node with another one.
        The data of the other node has priority.
        Also merges children if their fqn matches recursively
        """
        if self.get_fqn() != other.get_fqn():
            raise NotMergeableException(f"{self.get_fqn()} != {other.get_fqn()}")

        log.debug(f"{self.get_fqn()}, merging with='{other.get_fqn()}'")
        self_data = self.data.as_dict(exclude_fields=["fqn"])
        other_data = other.data.as_dict(exclude_fields=["fqn"])

        deep_update(self_data, other_data)
        self.data = get_vss_raw(self_data, self.get_fqn())

        child: VSSNode
        for child in other.children:
            match = self.get_child(child.get_fqn())
            if match:
                match.merge(child)
            else:
                child.parent = self

    def add_uuids(self) -> None:
        VSS_NAMESPACE = "vehicle_signal_specification"
        namespace_uuid = uuid.uuid5(uuid.NAMESPACE_OID, VSS_NAMESPACE)
        node: VSSNode
        for node in PreOrderIter(self):
            node.uuid = uuid.uuid5(namespace_uuid, node.get_fqn()).hex

    def get_instance_nodes(self) -> tuple[VSSNode, ...]:
        return findall(
            self,
            filter_=lambda node: isinstance(node.data, VSSDataBranch) and node.data.instances,
        )

    def get_node_with_fqn(self, fqn: str, sep: str = SEPARATOR) -> VSSNode | None:
        result = find(self, filter_=lambda n: n.get_fqn(sep) == fqn)
        if result:
            return result
        return None

    def connect(self, fqn: str, node: VSSNode) -> VSSNode | None:
        """
        Connects a node with a given fqn to this one
        It automatically generates missing branches in between.
        However, we are not generating valid branch entries
        (description is missing). This is on purpose so that
        the tree in the end fails if those values are not getting
        filled
        """
        connected = self.get_node_with_fqn(fqn)
        if connected:
            log.debug(f"Already connected: {fqn}")
            return connected
        target_fqn = get_expected_parent(fqn)
        if not target_fqn:
            return None
        target = self.get_node_with_fqn(target_fqn)
        if target:
            node.parent = target
            return target
        else:
            auto_node = VSSNode(
                get_name(target_fqn),
                target_fqn,
                {"type": "branch"},
            )
            node.parent = auto_node
            return self.connect(target_fqn, auto_node)

    def expand_instances(self) -> None:
        """
        Expanding all nodes that have configured
        "instances".
        It will generate new nodes below this one
        """
        instance_nodes = self.get_instance_nodes()
        instance_node: VSSNode
        iterations = 0
        n_instance_nodes = 0
        # We need to setup a loop here since it could be that
        # we add nodes that again have instances configured
        while instance_nodes:
            n_instance_nodes += len(instance_nodes)
            iterations += 1
            for instance_node in instance_nodes:
                log.debug(f"'{instance_node.get_fqn()}', expanding...")
                # Copy the reference node for creating instances
                instance_node_copy = deepcopy(instance_node)

                # PERF: instance_node_copy = instance_node.copy()
                # does not work here because it does not include copying
                # parents and therefore children fqns are different
                # However we are using the fqns to decide where to insert them
                # Fixing that would increase performance a bit since `deepcopy`
                # is very slow

                # Remove children from copy that should not be instantiatet
                for child in instance_node_copy.children:
                    if not getattr(child.data, "instantiate", True):
                        log.debug(f"'{child.get_fqn()}', removing from copy (instantiate=False)")
                        child.parent = None

                # Remove children from instance node that need to be put on created instances instead
                for child in instance_node.children:
                    if getattr(child.data, "instantiate", True):
                        log.debug(f"'{child.get_fqn()}', removing from node (instantiate=True)")
                        child.parent = None

                # Roots to attach generated nodes
                # Initialized with the instance node itself
                roots = [instance_node]
                log.debug(f"Roots: {[r.get_fqn() for r in roots]}")

                # We want to keep track of generated nodes
                # in order to append common original children
                # in the end
                generated_instance_nodes = []
                # On every iteration, we get back new nodes to attach new instances to (roots)
                # as well as the nodes that have been generated
                for instance in instance_node.data.instances:  # type: ignore
                    roots, generated = expand_instance(roots, instance_node_copy, instance)
                    generated_instance_nodes.extend(generated)

                # Since we do not want to append original children
                # to intermediate generated nodes, we filter for the leafs
                generated_instance_leaf_nodes = []
                for node in generated_instance_nodes:
                    if node.is_leaf:
                        generated_instance_leaf_nodes.append(node)

                # Appending all original children at the right place
                # Possibly overwriting content if wished
                add_expanded_instance_children(generated_instance_leaf_nodes, instance_node, instance_node_copy)

                instance_node.data.instances = []  # type: ignore
            instance_nodes = self.get_instance_nodes()
        if iterations:
            log.debug(f"Instances, iterations={iterations}, nodes={n_instance_nodes}")

    def delete_nodes(self, nodes: tuple[VSSNode]) -> None:
        """
        Deleting given nodes.
        It is not checked whether nodes are reachable from self!
        """
        size_before = self.size
        for node in nodes:
            log.debug(f"Deleting node: {node}")
            node.parent = None
        size_after = self.size
        if nodes:
            log.info(f"Nodes deleted, given={len(nodes)}, overall={size_before - size_after}")

    def get_naming_violations(self) -> list[list[str]]:
        """
        Gets a list of nodes that are violating the naming conventions
        It returns a list of fqn's and their violation reason
        """
        violations = []
        log.debug(f"Checking node name compliance for {self.name}")
        camel_case_pattern = re.compile("[A-Z][A-Za-z0-9]*$")
        for node in PreOrderIter(self):
            match = re.match(camel_case_pattern, node.name)
            if not match:
                violations.append([node.get_fqn(), "not CamelCase"])
            if isinstance(node.data, VSSDataDatatype):
                if node.data.datatype == Datatypes.BOOLEAN[0]:
                    if not node.name.startswith("Is") and not node.name.startswith("Has"):
                        violations.append([node.get_fqn(), "Not starting with 'Is' or 'Has'"])
        if violations:
            log.info(f"Naming violations: {len(violations)}")
        return violations

    def get_extra_attributes(self, allowed: tuple[str, ...]) -> list[list[str]]:
        """
        Gets a list of attributes that are not in the vss model
        and not explicitly allowed in the given list
        """
        violations = []
        for node in PreOrderIter(self):
            for field in node.data.get_extra_attributes():
                if field not in allowed:
                    violations.append([node.get_fqn(), field])
        if violations:
            log.warning(f"Attributes, violations={len(violations)}")
        return violations

    def as_flat_dict(self, with_extra_attributes: bool, extended_attributes: tuple[str, ...] = ()) -> dict[str, Any]:
        """
        Generates a flat dict and whether to include
        user attributes or not
        """
        data = {}
        node: VSSNode
        for node in PreOrderIter(self):
            key = node.get_fqn()
            data[key] = node.data.as_dict(with_extra_attributes, extended_attributes=extended_attributes)
            if node.uuid:
                data[key]["uuid"] = node.uuid
        return data


def get_expected_parent(name: str) -> str | None:
    """
    Returns the parent of a given fqn
    E.g. "A.B.C" -> "A.B"
    """
    parent = SEPARATOR.join(name.split(SEPARATOR)[:-1])
    if parent == name:
        return None
    if parent == "":
        return None
    return parent


def get_name(key: str) -> str:
    return key.split(SEPARATOR)[-1]


def find_children_ids(node_ids: list[str], name: str) -> list[str]:
    """
    Gets all direnct children of a given name.
    E.g. "A.B" -> ["A.B.C", "A.B.D"]
    """
    ids = []
    for i in node_ids:
        if get_expected_parent(i) == name:
            ids.append(i)
    return ids


def add_expanded_instance_children(roots: list[VSSNode], instance_root: VSSNode, instance_copy: VSSNode):
    """
    Adds initial children of node that started the instance expansion (instance_root)
    The initial state of the node has been freezed in instance_copy.
    The current points in the tree where to attach children is in roots
    """

    # We want to find nodes to add to the roots.
    # Nodes that area already in the instance_root
    # Should not be readded to the roots but should be replaced
    add = []
    child: VSSNode
    for child in instance_copy.children:
        match = instance_root.get_child(child.get_fqn())
        if not match:
            add.append(child)

    log.debug(f"Add to instances: {[n.get_fqn() for n in add]}")

    # Adding them..
    for root in roots:
        for a in add:
            c = a.copy()
            c.parent = root

    # Now searching for all initial children
    # that are in the current tree
    # Those are the ones we need to update
    change = []
    for child in instance_copy.children:
        match = instance_root.get_child(child.get_fqn())
        if match:
            change.append([match, child])

    log.debug(f"Change nodes: {[n[0].get_fqn() for n in change]}")

    for nodes in change:
        target = nodes[0]
        src = nodes[1]
        target.merge(src)
        # We found a place for the node to be changed
        # Exclude it from future processing
        src.parent = None


def expand_instance(
    roots: list[VSSNode],
    template: VSSNode,
    instance: list[str] | str,
) -> tuple[list[VSSNode], list[VSSNode]]:
    """
    Expands a given instance.
    roots represents the current points where to attach
    new nodes to. Depending on how many new nodes
    will be generated or how the instance was provided,
    we are returning the initial roots or new roots with the
    template contains a node copy for generating nodes
    generated nodes.
    """
    # The behavior is different depending how instances have been defined
    # Instances could be again a list of strings
    # We want to harmonize that
    # The info however is used to decide what new root points to return
    requested_instances = []
    if isinstance(instance, list):
        requested_instances = instance
    else:
        requested_instances = [instance]

    names = []
    # Node names can be given with a range syntax
    # such as Foo[1,2]asdf
    # We expand them here
    log.debug(f"Requested instances: {requested_instances}")
    for i in requested_instances:
        names.extend(expand_string(str(i)))
    nodes = []
    log.debug(f"Requested instance names: {names}")
    for name in names:
        for root in roots:
            # Need to copy the template so that we
            # are not messing with the same node
            node = template.copy()
            node.name = name
            node.data.instances = []  # type: ignore
            if isinstance(node.data, VSSDataBranch):
                node.data.is_instance = True
            node.parent = root
            nodes.append(node)
            node.children = []
    # New roots to attach to get returned
    # either when using the Row[1,2] syntax
    # or when specifying instances as a list entry
    # Otherwise next instance generation call will
    # attach nodes to the same roots again
    if len(names) > 1 or isinstance(instance, list):
        return nodes, nodes
    else:
        return roots, nodes


def count_seperator(s: str) -> int:
    return s.count(SEPARATOR)


def build_tree(data: dict[str, Any], connect_orphans: bool = False) -> tuple[VSSNode, dict[str, VSSNode]]:
    """
    Building a tree out of raw dictionary data.
    Also tries to find orphans and connects orphans
    if desired.
    """
    nodes: dict[str, VSSNode] = {}

    for k in sorted(data.keys(), key=count_seperator):
        v: Any = data.get(k)
        parent = get_expected_parent(k)
        node_name = get_name(k)
        node = VSSNode(node_name, k, v)
        # If this is a datatype tree we should add the
        # struct node as a datatype
        if isinstance(node.data, VSSDataStruct):
            dynamic_datatypes.add(k)

        # We connect a parent and children
        # Probably we should be fine only connecting
        # children since we are sorting for separators
        node.children = []
        if parent and parent in nodes:
            node.parent = nodes[parent]
        else:
            for child_id in find_children_ids(list(nodes.keys()), k):
                node.children.append(nodes[child_id])
        nodes[k] = node

    roots = []
    orphans = {}
    # Finding roots and orphans based on presence of a separator
    for fqn, node in nodes.items():
        if not node.parent:
            if SEPARATOR not in fqn:
                roots.append(node)
            else:
                orphans[fqn] = node

    if not roots:
        raise NoRootsException()

    if len(roots) > 1:
        raise MultipleRootsException(f"{[r.name for r in roots]}")

    root: VSSNode = roots[0]
    if connect_orphans:
        connected_fqns = []
        for fqn, orphan in orphans.items():
            connected = root.connect(fqn, orphan)
            if connected:
                connected_fqns.append(fqn)
        for fqn in connected_fqns:
            del orphans[fqn]

    if orphans:
        log.warning(f"Orphans: {len(orphans)}")

    log.debug(f"Tree, root='{root.name}', size={root.size}, height={root.height}")
    return root, orphans


def expand_string(s: str) -> list[str]:
    """
    Expands or unrolls a string with a range syntax
    definitions inside.

    Example: "abc[1,4]bar"
    Result:
    - abc1bar
    - abc2bar
    - abc3bar
    - abc4bar

    """
    pattern = r".*(\[(\d+),(\d+)\]).*"
    match = re.match(pattern, s)
    if not match:
        return [s]
    expanded = []
    if int(match.group(2)) > int(match.group(3)):
        raise InvalidExpansionEntryException(f"Invalid range: '{match.group(1)}'")
    for i in range(int(match.group(2)), int(match.group(3)) + 1):
        expanded.append(s.replace(match.group(1), str(i)))
    return expanded
