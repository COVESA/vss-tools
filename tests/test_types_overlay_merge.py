# Copyright (c) 2026 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import logging

import pytest
from vss_tools.datatypes import dynamic_datatypes
from vss_tools.main import TypesOverlayException, merge_types_overlay
from vss_tools.tree import VSSNode, build_tree


@pytest.fixture
def types_root():
    dynamic_datatypes.clear()
    data = {
        "Types": {"type": "branch", "description": "Root."},
        "Types.S": {"type": "struct", "description": "A struct."},
        "Types.S.x": {"type": "property", "description": "x.", "datatype": "double"},
    }
    root, orphans = build_tree(data)
    assert not orphans
    yield root
    dynamic_datatypes.clear()


def test_addition_is_silent(types_root: VSSNode, caplog):
    overlay = {"Types.S.y": {"type": "property", "description": "y.", "datatype": "uint8"}}
    with caplog.at_level(logging.WARNING):
        merge_types_overlay(types_root, overlay)
    assert caplog.records == []
    assert types_root.get_node_with_fqn("Types.S.y") is not None


def test_modification_is_logged(types_root: VSSNode, caplog):
    overlay = {"Types.S.x": {"datatype": "float"}}
    with caplog.at_level(logging.WARNING):
        merge_types_overlay(types_root, overlay)
    messages = [r.getMessage() for r in caplog.records]
    assert any("Types.S.x" in m and "datatype" in m and "'double' -> 'float'" in m for m in messages)
    node = types_root.get_node_with_fqn("Types.S.x")
    assert node is not None
    assert node.data.as_dict()["datatype"] == "float"


def test_same_value_is_not_logged(types_root: VSSNode, caplog):
    overlay = {"Types.S.x": {"datatype": "double"}}
    with caplog.at_level(logging.WARNING):
        merge_types_overlay(types_root, overlay)
    assert caplog.records == []


def test_new_struct_is_registered_as_datatype(types_root: VSSNode):
    overlay = {"Types.T": {"type": "struct", "description": "New struct."}}
    merge_types_overlay(types_root, overlay)
    assert "Types.T" in dynamic_datatypes


def test_parent_in_overlay_regardless_of_order(types_root: VSSNode):
    overlay = {
        "Types.Sub.T": {"type": "struct", "description": "New struct."},
        "Types.Sub": {"type": "branch", "description": "Header."},
    }
    merge_types_overlay(types_root, overlay)
    node = types_root.get_node_with_fqn("Types.Sub.T")
    assert node is not None
    assert node.parent is types_root.get_node_with_fqn("Types.Sub")


def test_orphans(types_root: VSSNode):
    overlay = {"Types.Sub.T": {"type": "struct", "description": "New struct."}}
    with pytest.raises(TypesOverlayException, match="orphans"):
        merge_types_overlay(types_root, overlay)


def test_wildcards_not_supported(types_root: VSSNode):
    with pytest.raises(TypesOverlayException, match="Wildcards"):
        merge_types_overlay(types_root, {"Types.*": {"description": "x"}})


def test_wrong_root(types_root: VSSNode):
    with pytest.raises(TypesOverlayException, match="types root"):
        merge_types_overlay(types_root, {"Other.S": {"type": "struct", "description": "x"}})
