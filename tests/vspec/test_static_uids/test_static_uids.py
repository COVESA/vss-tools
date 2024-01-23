# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert vspec files to various other formats
#

import os
import shlex
from typing import Dict

import pytest
import yaml

import vspec
import vspec2x
import vspec.vssexporters.vss2id as vss2id
from vspec.model.constants import VSSDataType, VSSTreeType, VSSUnit
from vspec.model.vsstree import VSSNode
from vspec.utils.idgen_utils import get_all_keys_values

# HELPERS


def get_cla_test(test_file: str):
    return (
        "../../../vspec2id.py "
        + test_file
        + " ./out.vspec --validate-static-uid "
        + "./validation_vspecs/validation.vspec "
        + "--only-validate-no-export"
    )


def get_cla_validation(validation_file: str):
    return (
        "../../../vspec2id.py ./test_vspecs/test.vspec ./out.vspec "
        "--validate-static-uid " + validation_file
    )


def get_test_node(
    node_name: str,
    unit: str,
    datatype: VSSDataType,
    allowed: str,
    minimum: str,
    maximum: str,
) -> VSSNode:
    source = {
        "description": "some desc",
        "type": "branch",
        "$file_name$": "testfile",
    }
    node = VSSNode(node_name, source, VSSTreeType.SIGNAL_TREE.available_types())
    node.unit = VSSUnit(unit)
    node.data_type_str = datatype.value
    node.validate_and_set_datatype()
    node.allowed = allowed
    node.min = minimum
    node.max = maximum

    return node


# FIXTURES


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


# UNIT TESTS


@pytest.mark.parametrize(
    "node_name, unit, datatype, allowed, minimum, maximum, result_static_uid",
    [
        ("TestNode", "m", VSSDataType.UINT16, "", 0, 10000, "A1D565B2"),
        ("TestNode", "mm", VSSDataType.UINT32, "", "", "", "B5D7A8FA"),
        ("TestUnit", "degrees/s", VSSDataType.FLOAT, "", "", "", "DEA9138C"),
        ("TestMinMax", "percent", VSSDataType.UINT8, "", 0, 100, "88FC5491"),
        ("TestEnum", "m", VSSDataType.STRING, ["YES, NO"], "", "", "06AEB370"),
    ],
)
def test_generate_id(
    node_name: str,
    unit: str,
    datatype: VSSDataType,
    allowed: str,
    minimum: str,
    maximum: str,
    result_static_uid: str,
):
    node = get_test_node(node_name, unit, datatype, allowed, minimum, maximum)
    result, _ = vss2id.generate_split_id(node, id_counter=0, strict_mode=False)

    assert result == result_static_uid


@pytest.mark.parametrize(
    "node_name_case_sensitive, node_name_case_insensitive, strict_mode",
    [
        ("TestNode", "testnode", False),
        ("TestNode", "testnode", True),
    ],
)
def test_strict_mode(
    node_name_case_sensitive: str, node_name_case_insensitive: str, strict_mode: bool
):
    node_case_sensitive = get_test_node(
        node_name=node_name_case_sensitive,
        unit="m",
        datatype=VSSDataType.FLOAT,
        allowed="",
        minimum="",
        maximum="",
    )
    result_case_sensitive, _ = vss2id.generate_split_id(
        node_case_sensitive, id_counter=0, strict_mode=strict_mode
    )

    node_case_insensitive = get_test_node(
        node_name=node_name_case_insensitive,
        unit="m",
        datatype=VSSDataType.FLOAT,
        allowed="",
        minimum="",
        maximum="",
    )
    result_case_insensitive, _ = vss2id.generate_split_id(
        node_case_insensitive, id_counter=0, strict_mode=strict_mode
    )

    if strict_mode:
        assert result_case_sensitive != result_case_insensitive
    else:
        assert result_case_sensitive == result_case_insensitive


@pytest.mark.parametrize(
    "test_file, validation_file",
    [("test_vspecs/test.vspec", "./validation.yaml")],
)
def test_export_node(
    request: pytest.FixtureRequest,
    test_file: str,
    validation_file: str,
):
    dir_path = os.path.dirname(request.path)
    vspec_file = os.path.join(dir_path, test_file)

    vspec.load_units(vspec_file, [os.path.join(dir_path, "test_vspecs/units.yaml")])
    tree = vspec.load_tree(
        vspec_file, include_paths=["."], tree_type=VSSTreeType.SIGNAL_TREE
    )
    yaml_dict: Dict[str, str] = {}
    vss2id.export_node(yaml_dict, tree, id_counter=0, strict_mode=False)

    result_dict: Dict[str, str]
    with open(os.path.join(dir_path, validation_file)) as f:
        result_dict = yaml.load(f, Loader=yaml.FullLoader)

    assert result_dict.keys() == yaml_dict.keys()
    assert result_dict == yaml_dict


@pytest.mark.parametrize(
    "children_names",
    [
        ["ChildNode", "ChildNode"],
        ["ChildNode", "ChildNodeDifferentName"],
    ],
)
def test_duplicate_hash(caplog: pytest.LogCaptureFixture, children_names: list):
    tree = get_test_node("TestNode", "m", VSSDataType.UINT32, "", "", "")
    child_node = get_test_node(children_names[0], "m", VSSDataType.UINT32, "", "", "")
    child_node2 = get_test_node(children_names[1], "m", VSSDataType.UINT32, "", "", "")
    tree.children = [child_node, child_node2]

    yaml_dict: Dict[str, dict] = {}
    if children_names[0] == children_names[1]:
        # assert system exit and log
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            vss2id.export_node(yaml_dict, tree, id_counter=0, strict_mode=False)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == -1
        assert len(caplog.records) == 1 and all(
            log.levelname == "CRITICAL" for log in caplog.records
        )
    else:
        # assert all IDs different
        vss2id.export_node(yaml_dict, tree, id_counter=0, strict_mode=False)
        assigned_ids: list = []
        for key, value in get_all_keys_values(yaml_dict):
            if not isinstance(value, dict) and key == "staticUID":
                assigned_ids.append(value)
        assert len(assigned_ids) == len(set(assigned_ids))


# INTEGRATION TESTS


@pytest.mark.usefixtures("change_test_dir")
def test_full_script(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 0


@pytest.mark.usefixtures("change_test_dir")
def test_semantic(caplog: pytest.LogCaptureFixture):
    validation_file: str = "./validation_vspecs/validation_semantic_change.vspec"
    clas = shlex.split(get_cla_validation(validation_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "SEMANTIC NAME CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_vss_path(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_vss_path.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])
    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "PATH CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_unit(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_unit.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_datatype(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_datatype.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "BREAKING CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_name_datatype(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_name_datatype.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 2 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for i, record in enumerate(caplog.records):
        if i % 2 == 0:
            assert "ADDED ATTRIBUTE" in record.msg
        else:
            assert "DELETED ATTRIBUTE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_deprecation(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_deprecation.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "DEPRECATION MSG CHANGE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_description(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_description.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "DESCRIPTION MISMATCH" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_added_attribute(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_added_attribute.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "ADDED ATTRIBUTE" in record.msg


@pytest.mark.usefixtures("change_test_dir")
def test_deleted_attribute(caplog: pytest.LogCaptureFixture):
    test_file: str = "./test_vspecs/test_deleted_attribute.vspec"
    clas = shlex.split(get_cla_test(test_file))
    vspec2x.main(["--format", "idgen"] + clas[1:])

    assert len(caplog.records) == 1 and all(
        log.levelname == "WARNING" for log in caplog.records
    )
    for record in caplog.records:
        assert "DELETED ATTRIBUTE" in record.msg
