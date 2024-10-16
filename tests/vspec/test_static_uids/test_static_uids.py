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
import subprocess
from pathlib import Path
from typing import Dict

import pytest
import vss_tools.exporters.id as vss2id
import yaml
from vss_tools.datatypes import Datatypes
from vss_tools.main import get_trees
from vss_tools.tree import VSSNode
from vss_tools.utils.idgen_utils import get_all_keys_values

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def get_cla_test(test_file: Path, tmp_path: Path, overlay: str | None = None):
    args = f"--vspec {test_file}"
    output = tmp_path / "out.vspec"
    if overlay:
        args += f" -l {overlay}"
    validation = HERE / "validation_vspecs/validation.vspec"
    units = HERE / "test_vspecs/units.yaml"
    args += f" --output {output} --validate-static-uid {validation} -u {units} -q {TEST_QUANT}"
    return args


def get_test_node(
    node_name,
    unit,
    datatype,
    allowed,
    minimum,
    maximum,
) -> VSSNode:
    source = {
        "description": "some desc",
        "type": "branch",
        "unit": unit,
        "datatype": datatype,
        "min": minimum,
        "max": maximum,
        "allowed": allowed,
    }
    return VSSNode(node_name, None, source)


@pytest.mark.parametrize(
    "node_name, unit, datatype, allowed, minimum, maximum, result_static_uid",
    [
        ("TestNode", "m", Datatypes.UINT16[0], [], 0, 10000, "A1D565B2"),
        ("TestNode", "mm", Datatypes.UINT32[0], [], None, None, "B5D7A8FA"),
        ("TestUnit", "degrees/s", Datatypes.FLOAT[0], [], None, None, "DEA9138C"),
        ("TestMinMax", "percent", Datatypes.UINT8[0], [], 0, 100, "88FC5491"),
        ("TestEnum", "m", Datatypes.STRING[0], ["YES, NO"], None, None, "06AEB370"),
    ],
)
def test_generate_id(
    node_name: str,
    unit: str,
    datatype: Datatypes,
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
def test_strict_mode(node_name_case_sensitive: str, node_name_case_insensitive: str, strict_mode: bool):
    node_case_sensitive = get_test_node(
        node_name=node_name_case_sensitive,
        unit="m",
        datatype=Datatypes.FLOAT[0],
        allowed=[],
        minimum=None,
        maximum=None,
    )
    result_case_sensitive, _ = vss2id.generate_split_id(node_case_sensitive, id_counter=0, strict_mode=strict_mode)

    node_case_insensitive = get_test_node(
        node_name=node_name_case_insensitive,
        unit="m",
        datatype=Datatypes.FLOAT[0],
        allowed=[],
        minimum=None,
        maximum=None,
    )
    result_case_insensitive, _ = vss2id.generate_split_id(node_case_insensitive, id_counter=0, strict_mode=strict_mode)

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
    validation_file,
):
    vspec_file = HERE / test_file
    validation_file = HERE / validation_file
    unit_files = (HERE / "test_vspecs/units.yaml",)

    tree, _ = get_trees(vspec=vspec_file, units=unit_files, quantities=(TEST_QUANT,))
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
    tree = get_test_node("TestNode", "m", Datatypes.UINT32[0], "", "", "")
    child_node = get_test_node(children_names[0], "m", Datatypes.UINT32[0], "", "", "")
    child_node2 = get_test_node(children_names[1], "m", Datatypes.UINT32[0], "", "", "")
    tree.children = [child_node, child_node2]

    yaml_dict: Dict[str, dict] = {}
    if children_names[0] == children_names[1]:
        # assert system exit and log
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            vss2id.export_node(yaml_dict, tree, id_counter=0, strict_mode=False)
        assert pytest_wrapped_e.type is SystemExit
        assert pytest_wrapped_e.value.code == -1
        assert len(caplog.records) == 1 and all(log.levelname == "CRITICAL" for log in caplog.records)
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
    test_file = HERE / "test_vspecs/test.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(test_file, tmp_path))
    cmd += clas
    process = subprocess.run(cmd)
    assert process.returncode == 0


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
    args = f"vspec export id --vspec {spec} --output {output}"
    args += f" --validate-static-uid {validation} -q {TEST_QUANT}"
    process = subprocess.run(args.split(), capture_output=True, text=True)
    assert "SEMANTIC NAME CHANGE" in process.stdout


def test_vss_path(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_vss_path.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert "PATH CHANGE" in process.stdout


def test_unit(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_unit.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert "BREAKING CHANGE" in process.stdout


def test_datatype(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_datatype.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert "BREAKING CHANGE" in process.stdout


def test_name_datatype(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_name_datatype.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert "ADDED ATTRIBUTE" in process.stdout
    assert "DELETED ATTRIBUTE" in process.stdout


def test_deprecation(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_deprecation.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert "DEPRECATION MSG CHANGE" in process.stdout


def test_description(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_description.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert "DESCRIPTION MISMATCH" in process.stdout


def test_added_attribute(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_added_attribute.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert "ADDED ATTRIBUTE" in process.stdout

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    keys: list = [key for key, _ in get_all_keys_values(result)]
    assert "A.B.NewNode" in keys


def test_deleted_attribute(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test_deleted_attribute.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert "DELETED ATTRIBUTE" in process.stdout

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    keys: list = [key for key, _ in get_all_keys_values(result)]
    assert "A.B.Max" not in keys


def test_overlay(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test.vspec"
    overlay = HERE / "test_vspecs/test_overlay.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path, overlay))
    cmd += clas
    process = subprocess.run(cmd, capture_output=True, text=True)
    print(process.stdout)
    assert "ADDED ATTRIBUTE" in process.stdout

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    keys: list = [key for key, _ in get_all_keys_values(result)]
    assert "A.B.OverlayNode" in keys


def test_const_id(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test.vspec"
    overlay = HERE / "test_vspecs/test_const_id.vspec"

    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path, overlay))
    cmd += clas
    subprocess.run(cmd, capture_output=True, text=True)

    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)
    for key, value in get_all_keys_values(result):
        if key == "A.B.Int32":
            assert value["staticUID"] == "0x00112233"


def test_iterated_file(caplog: pytest.LogCaptureFixture, tmp_path):
    spec = HERE / "test_vspecs/test.vspec"
    cmd = "vspec export id".split()
    clas = shlex.split(get_cla_test(spec, tmp_path))
    cmd += clas
    subprocess.run(cmd, capture_output=True, text=True)
    output = tmp_path / "out.vspec"
    result = yaml.load(open(output), Loader=yaml.FullLoader)

    # run again on out.vspec to check if it all hashed attributes were exported correctly
    clas = shlex.split(get_cla_test(output, tmp_path))
    subprocess.run(cmd, capture_output=True, text=True)

    output = tmp_path / "out.vspec"
    result_iteration = yaml.load(open(output), Loader=yaml.FullLoader)

    assert result == result_iteration
