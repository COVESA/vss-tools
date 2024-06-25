#!/usr/bin/env python3

# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest

from vss_tools.vspec.model.constants import VSSTreeType
from vss_tools.vspec.model.vsstree import VSSNode


@pytest.mark.parametrize("type_name, is_signal_tree, is_default_supported", [
    ("attribute", True, True),
    ("actuator", True, True),
    ("sensor", True, True),
    ("branch", True, False),
    ("branch", False, False),
    ("struct", False, False),
    ("property", False, True)
    ])
def test_default(type_name: str, is_signal_tree: bool, is_default_supported: bool):
    """
    Verify that tooling complains if "default" is used where it should not be used
    """
    source = {
                "description": "some desc",
                "type": type_name,
                "$file_name$": "testfile",
                "default": 1234}

    if type_name in ["attribute", "sensor", "actuator", "property"]:
        source["datatype"] = "uint8"

    if is_signal_tree:
        type_set = VSSTreeType.SIGNAL_TREE.available_types()
    else:
        type_set = VSSTreeType.DATA_TYPE_TREE.available_types()

    if type_name in ["property"]:
        # Create a struct above
        source_struct = {
                "description": "some desc",
                "type": "struct",
                "$file_name$": "testfile"}

        parent = VSSNode(
                "TestStruct",
                source_struct,
                type_set)
    else:
        parent = None

    node = VSSNode(
                "Test",
                source,
                type_set,
                parent=parent)

    assert node is not None

    if is_default_supported:
        node.verify_attributes(True)
    else:
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            node.verify_attributes(True)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == -1
