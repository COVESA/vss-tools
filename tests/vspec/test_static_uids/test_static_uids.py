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

import shlex
from typing import Dict

import pytest
import vss_tools.vspec as vspec

import vss_tools.vspec.exporters.vss2id as vss2id
import vss_tools.vspec2id as vspec2id
import yaml

from vss_tools.vspec.model.constants import VSSDataType, VSSTreeType, VSSUnit
from vss_tools.vspec.model.vsstree import VSSNode
from vss_tools.vspec.exporters.idgen_utils import get_all_keys_values

from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def get_cla_test(test_file: str, tmp_path: Path, overlay: str | None = None):
    args = f"vspec2id {test_file}"
    output = tmp_path / "out.vspec"
    if overlay:
        args += f" -o {overlay}"
    validation = HERE / "validation_vspecs/validation.vspec"
    units = HERE / "test_vspecs/units.yaml"
    args += f" {output} --validate-static-uid {validation} -u {units}"
    return args


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
    node = VSSNode(node_name, source,
                   VSSTreeType.SIGNAL_TREE.available_types())
    node.unit = VSSUnit(unit)
    node.data_type_str = datatype.value
    node.validate_and_set_datatype()
    node.allowed = allowed
    node.min = minimum
    node.max = maximum

    return node


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
    [("test_vspecs/test.vspec", "validation.yaml")],
)
def test_export_node(
    request: pytest.FixtureRequest,
    test_file: str,
    validation_file: str,
):
    vspec_file = HERE / test_file
    validation_file = HERE / validation_file
    units = str(HERE / "test_vspecs/units.yaml")

    vspec.load_units(str(vspec_file), [units])
    tree = vspec.load_tree(
        str(vspec_file), include_paths=["."], tree_type=VSSTreeType.SIGNAL_TREE
    )
    yaml_dict: Dict[str, str] = {}
    vss2id.export_node(yaml_dict, tree, id_counter=0, strict_mode=False)

    result_dict: Dict[str, str]
    with open(validation_file) as f:
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
    child_node = get_test_node(
        children_names[0], "m", VSSDataType.UINT32, "", "", "")
    child_node2 = get_test_node(
        children_names[1], "m", VSSDataType.UINT32, "", "", "")
    tree.children = [child_node, child_node2]

    yaml_dict: Dict[str, dict] = {}
    if children_names[0] == children_names[1]:
        # assert system exit and log
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            vss2id.export_node(
                yaml_dict, tree, id_counter=0, strict_mode=False)
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


def test_full_script(caplog: pytest.LogCaptureFixture, tmp_path):
    test_file: str = str(HERE / "test_vspecs/test.vspec")
    clas = shlex.split(get_cla_test(test_file, tmp_path))
    vspec2id.main(clas[1:])

    assert len(caplog.records) == 9


@pytest.mark.parametrize(
    "validation_file",
    [
        "validation_vspecs/validation_semantic_change_1.vspec",
        "validation_vspecs/validation_semantic_change_2.vspec",
    ],
)
def test_semantic(caplog: pytest.LogCaptureFixture, validation_file: str, tmp_path):
    spec = HERE / "test_vspecs/test.vspec"
    output = tmp_path / "out.vspec"
    validation = HERE / validation_file
    args = f"vspec2id {spec} {output} --validate-static-uid {validation}"
    clas = shlex.split(args)
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "SEMANTIC NAME CHANGE" in record.msg


def test_vss_path(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_vss_path.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "PATH CHANGE" in record.msg


def test_unit(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_unit.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 2
    for record in warning_logs:
        assert "BREAKING CHANGE" in record.msg


def test_datatype(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_datatype.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "BREAKING CHANGE" in record.msg


def test_name_datatype(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_name_datatype.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 2
    for i, record in enumerate(warning_logs):
        if i % 2 == 0:
            assert "ADDED ATTRIBUTE" in record.msg
        else:
            assert "DELETED ATTRIBUTE" in record.msg


def test_deprecation(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_deprecation.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "DEPRECATION MSG CHANGE" in record.msg


def test_description(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_description.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "DESCRIPTION MISMATCH" in record.msg


def test_added_attribute(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_added_attribute.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "ADDED ATTRIBUTE" in record.msg

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    keys: list = [key for key, _ in get_all_keys_values(result)]
    assert "A.B.NewNode" in keys


def test_deleted_attribute(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_deleted_attribute.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "DELETED ATTRIBUTE" in record.msg

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    keys: list = [key for key, _ in get_all_keys_values(result)]
    assert "A.B.Max" not in keys


def test_overlay(caplog: pytest.LogCaptureFixture, tmp_path):

    spec = HERE / "test_vspecs/test.vspec"
    overlay = HERE / "test_vspecs/test_overlay.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path, overlay))
    vspec2id.main(clas[1:])

    warning_logs = [log for log in caplog.records if log.levelname == "WARNING"]
    assert len(warning_logs) == 1
    for record in warning_logs:
        assert "ADDED ATTRIBUTE" in record.msg

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    keys: list = [key for key, _ in get_all_keys_values(result)]
    assert "A.B.OverlayNode" in keys


def test_const_id(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test.vspec"
    overlay = HERE / "test_vspecs/test_const_id.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path, overlay))
    vspec2id.main(clas[1:])

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    for key, value in get_all_keys_values(result):
        if key == "A.B.Int32":
            assert value["staticUID"] == "0x00112233"


def test_iterated_file(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test.vspec"
    clas = shlex.split(get_cla_test(spec, tmp_path))
    vspec2id.main(clas[1:])

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)

    # run again on out.vspec to check if it all hashed attributes were exported correctly
    clas = shlex.split(get_cla_test(output, tmp_path))
    vspec2id.main(clas[1:])

    output = tmp_path / "out.vspec"
    result_iteration = yaml.load(open(output), Loader=yaml.FullLoader)

    assert result == result_iteration
