# Copyright (c) 2024 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

#
# Convert vspec files to various other formats
#


import subprocess
from pathlib import Path
from typing import Optional

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def get_cla(test_file: str, out_file: str, overlay: Optional[str]):
    args = f"-u {TEST_UNITS} -q {TEST_QUANT}"
    if overlay:
        args += f" -l {overlay}"
    args += f" --vspec {test_file} --output {out_file}"
    return args


@pytest.mark.parametrize(
    "exporter, out_file",
    [
        ("vspec export binary", "out.bin"),
        ("vspec export csv", "out.csv"),
        ("vspec export ddsidl", "out.idl"),
        ("vspec export franca", "out.fidl"),
        ("vspec export graphql", "out.graphql"),
        ("vspec export json", "out.json"),
        ("vspec export jsonschema", "out.jsonschema"),
        ("vspec export protobuf", "out.pb"),
        ("vspec export yaml", "out.yaml"),
    ],
)
@pytest.mark.parametrize(
    "overlay",
    [
        None,
        "test_files/test_del_node_overlay.vspec",
    ],
)
def test_deleted_node(exporter: str, out_file: str, overlay: Optional[str], tmp_path):
    spec: Path
    if overlay:
        spec = HERE / "test_files/test.vspec"
    else:
        spec = HERE / "test_files/test_deleted_node.vspec"

    output = tmp_path / out_file
    ov = None
    if overlay:
        ov = str(HERE / overlay)
    cmd = exporter.split() + get_cla(spec, str(output), ov).split()
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert process.returncode == 0
    result = output.read_text()

    remaining_nodes = [
        "A.Float",
        "A.Int16",
        "A.String",
        "A.StringArray",
        "A.B",
        "A.B.NewName",
        "A.B.IsLeaf",
        "A.B.Min",
        "A.B.Max",
        "A.C",
        "A.C.Instance1",
        "A.C.Instance1.Test",
        "A.C.Instance2",
        "A.C.Instance2.Test",
    ]
    if exporter in [
        "vspec export binary",
        "vspec export ddsidl",
        "vspec export json",
        "vspec export jsonschema",
        "vspec export protobuf",
    ]:
        assert "A.B.Int32".split(".")[-1] not in result
        remaining_nodes = [node.split(".")[-1] for node in remaining_nodes]
        for node in remaining_nodes:
            assert node in result
    if exporter in ["vspec export graphql"]:
        remaining_nodes = [
            "float",
            "int16",
            "string",
            "stringArray",
            "A_B",
            "newName",
            "isLeaf",
            "min",
            "max",
            "A_C",
            "A_C_Instance_Enum",
            "test",
        ]

        assert "int32:" not in result
        print(result)
        for node in remaining_nodes:
            assert node in result
    else:
        assert "A.B.Int32" not in result
        for node in remaining_nodes:
            assert node in result


@pytest.mark.parametrize(
    "exporter, out_file",
    [
        ("vspec export binary", "out.bin"),
        ("vspec export csv", "out.csv"),
        ("vspec export ddsidl", "out.idl"),
        ("vspec export franca", "out.fidl"),
        ("vspec export graphql", "out.graphql"),
        ("vspec export json", "out.json"),
        ("vspec export jsonschema", "out.jsonschema"),
        ("vspec export protobuf", "out.pb"),
        ("vspec export yaml", "out.yaml"),
    ],
)
@pytest.mark.parametrize(
    "overlay",
    [
        None,
        "test_files/test_del_branch_overlay.vspec",
    ],
)
def test_deleted_branch(exporter: str, out_file: str, overlay: Optional[str], tmp_path):
    spec: Path
    if overlay:
        spec = HERE / "test_files/test.vspec"
    else:
        spec = HERE / "test_files/test_deleted_branch.vspec"

    output = tmp_path / out_file
    ov = None
    if overlay:
        ov = str(HERE / overlay)
    cmd = exporter.split() + get_cla(spec, str(output), ov).split()
    process = subprocess.run(cmd, capture_output=True, text=True)
    assert process.returncode == 0
    result_file = output.read_text()

    remaining_nodes = [
        "A.Float",
        "A.Int16",
        "A.String",
        "A.StringArray",
        "A.C",
        "A.C.Instance1",
        "A.C.Instance1.Test",
        "A.C.Instance2",
        "A.C.Instance2.Test",
    ]

    if exporter in [
        "vspec export binary",
        "vspec export ddsidl",
        "vspec export json",
        "vspec export jsonschema",
        "vspec export protobuf",
    ]:
        assert "A.B".split(".")[-1] not in result_file
        remaining_nodes = [node.split(".")[-1] for node in remaining_nodes]
        for node in remaining_nodes:
            assert node in result_file
    elif exporter == "vspec export graphql":
        remaining_nodes = [
            "float",
            "int16",
            "string",
            "stringArray",
            "A_C",
            "INSTANCE1",
            "test",
            "INSTANCE2",
            "A_C_Instance_Enum",
        ]
        assert "A.B".replace(".", "_") not in result_file
        remaining_nodes = [node.replace(".", "_") for node in remaining_nodes]
        for node in remaining_nodes:
            assert node in result_file
    else:
        assert "A.B" not in result_file
        for node in remaining_nodes:
            assert node in result_file


@pytest.mark.parametrize(
    "exporter, out_file",
    [
        ("vspec export binary", "out.bin"),
        ("vspec export csv", "out.csv"),
        ("vspec export ddsidl", "out.idl"),
        ("vspec export franca", "out.fidl"),
        ("vspec export graphql", "out.graphql"),
        ("vspec export json", "out.json"),
        ("vspec export jsonschema", "out.jsonschema"),
        ("vspec export protobuf", "out.pb"),
        ("vspec export yaml", "out.yaml"),
    ],
)
@pytest.mark.parametrize(
    "overlay",
    [
        "test_files/test_del_instance_overlay.vspec",
    ],
)
def test_deleted_instance(
    caplog: pytest.LogCaptureFixture,
    exporter: str,
    out_file: str,
    overlay: str,
    tmp_path,
):
    spec = HERE / "test_files/test.vspec"
    output = tmp_path / out_file

    ov = HERE / overlay
    cmd = exporter.split() + get_cla(spec, str(output), str(ov)).split()

    process = subprocess.run(cmd, capture_output=True, text=True)
    print(process.stdout)
    print(process.stderr)

    if "wrong" in overlay:
        assert process.returncode != 0
    else:
        print(process.stdout)
        result_file = output.read_text()

        remaining_nodes = [
            "A.Float",
            "A.Int16",
            "A.String",
            "A.StringArray",
            "A.B",
            "A.B.NewName",
            "A.B.IsLeaf",
            "A.B.Min",
            "A.B.Max",
            "A.C",
            "A.C.Instance1",
            "A.C.Instance1.Test",
        ]

        if exporter in [
            "vspec export binary",
            "vspec export ddsidl",
            "vspec export json",
            "vspec export jsonschema",
            "vspec export protobuf",
        ]:
            assert "A.C.Instance2".split(".")[-1] not in result_file
            remaining_nodes = [node.split(".")[-1] for node in remaining_nodes]
            for node in remaining_nodes:
                assert node in result_file
        elif exporter == "vspec export graphql":
            print(result_file)
            remaining_nodes = [
                "float",
                "int16",
                "string",
                "stringArray",
                "A_B",
                "newName",
                "isLeaf",
                "min",
                "max",
                "A_C",
                "INSTANCE1",
                "test",
            ]
            assert "Instance2" not in result_file
            for node in remaining_nodes:
                assert node in result_file
        else:
            assert "A.C.Instance2" not in result_file
            for node in remaining_nodes:
                assert node in result_file
