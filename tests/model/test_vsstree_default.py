#!/usr/bin/env python3

#
# (C) 2023 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

import pytest

from vspec.model.constants import VSSTreeType
from vspec.model.vsstree import VSSNode


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


@pytest.mark.parametrize("type_name, is_signal_tree, is_default_supported", [
    ("attribute", True, True),
    ("actuator", True, True),
    ("sensor", True, True),
    ("branch", True, False),
    ("branch", False, False),
    ("struct", False, False),
    ("property", False, True)
    ])
def test_default(type_name: str, is_signal_tree: bool, is_default_supported: bool, change_test_dir):
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
