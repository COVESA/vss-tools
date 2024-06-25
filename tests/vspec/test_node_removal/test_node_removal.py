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


import shlex
from typing import Optional

import pytest

from pathlib import Path
import vss_tools.vspec2binary as vspec2binary  # noqa: F401
import vss_tools.vspec2csv as vspec2csv  # noqa: F401
import vss_tools.vspec2ddsidl as vspec2ddsidl  # noqa: F401
import vss_tools.vspec2franca as vspec2franca  # noqa: F401
import vss_tools.vspec2graphql as vspec2graphql  # noqa: F401
import vss_tools.vspec2json as vspec2json  # noqa: F401
import vss_tools.vspec2jsonschema as vspec2jsonschema  # noqa: F401
import vss_tools.vspec2protobuf as vspec2protobuf  # noqa: F401
import vss_tools.vspec2yaml as vspec2yaml  # noqa: F401

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def get_cla(test_file: str, out_file: str, overlay: Optional[str]):
    args = f"-u {TEST_UNITS}"
    if overlay:
        args += f" -o {overlay}"
    args += f" {test_file} {out_file}"
    return args


@pytest.mark.parametrize(
    "exporter, out_file",
    [
        ("vspec2binary", "out.bin"),
        ("vspec2csv", "out.csv"),
        ("vspec2ddsidl", "out.idl"),
        ("vspec2franca", "out.fidl"),
        ("vspec2graphql", "out.graphql"),
        ("vspec2json", "out.json"),
        ("vspec2jsonschema", "out.jsonschema"),
        ("vspec2protobuf", "out.pb"),
        ("vspec2yaml", "out.yaml"),
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
    clas = shlex.split(get_cla(spec, str(output), ov))
    eval(f"{exporter}.main({clas})")
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
        "vspec2binary",
        "vspec2ddsidl",
        "vspec2json",
        "vspec2jsonschema",
        "vspec2protobuf",
    ]:
        assert "A.B.Int32".split(".")[-1] not in result
        remaining_nodes = [node.split(".")[-1] for node in remaining_nodes]
        for node in remaining_nodes:
            assert node in result
    if exporter == "vspec2graphql":
        assert "A.B.Int32".replace(".", "_") not in result
        remaining_nodes = [node.replace(".", "_") for node in remaining_nodes]
        for node in remaining_nodes:
            assert node in result
    else:
        assert "A.B.Int32" not in result
        for node in remaining_nodes:
            assert node in result


@pytest.mark.parametrize(
    "exporter, out_file",
    [
        ("vspec2binary", "out.bin"),
        ("vspec2csv", "out.csv"),
        ("vspec2ddsidl", "out.idl"),
        ("vspec2franca", "out.fidl"),
        ("vspec2graphql", "out.graphql"),
        ("vspec2json", "out.json"),
        ("vspec2jsonschema", "out.jsonschema"),
        ("vspec2protobuf", "out.pb"),
        ("vspec2yaml", "out.yaml"),
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
    clas = shlex.split(get_cla(spec, str(output), ov))

    eval(f"{exporter}.main({clas})")
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
        "vspec2binary",
        "vspec2ddsidl",
        "vspec2json",
        "vspec2jsonschema",
        "vspec2protobuf",
    ]:
        assert "A.B".split(".")[-1] not in result_file
        remaining_nodes = [node.split(".")[-1] for node in remaining_nodes]
        for node in remaining_nodes:
            assert node in result_file
    elif exporter == "vspec2graphql":
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
        ("vspec2binary", "out.bin"),
        ("vspec2csv", "out.csv"),
        ("vspec2ddsidl", "out.idl"),
        ("vspec2franca", "out.fidl"),
        ("vspec2graphql", "out.graphql"),
        ("vspec2json", "out.json"),
        ("vspec2jsonschema", "out.jsonschema"),
        ("vspec2protobuf", "out.pb"),
        ("vspec2yaml", "out.yaml"),
    ],
)
@pytest.mark.parametrize(
    "overlay",
    [
        "test_files/test_del_instance_overlay.vspec",
        "test_files/test_del_wrong_instance_overlay.vspec",
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
    clas = shlex.split(get_cla(spec, str(output), str(HERE / overlay)))

    if "wrong" in overlay:
        with pytest.raises(SystemExit) as exporter_result:
            eval(f"{exporter}.main({clas})")
        assert exporter_result.type == SystemExit
        assert exporter_result.value.code == -1
    else:
        eval(f"{exporter}.main({clas})")
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
            "vspec2binary",
            "vspec2ddsidl",
            "vspec2json",
            "vspec2jsonschema",
            "vspec2protobuf",
        ]:
            assert "A.C.Instance2".split(".")[-1] not in result_file
            remaining_nodes = [node.split(".")[-1] for node in remaining_nodes]
            for node in remaining_nodes:
                assert node in result_file
        elif exporter == "vspec2graphql":
            assert "A.C.Instance2".replace(".", "_") not in result_file
            remaining_nodes = [node.replace(".", "_")
                               for node in remaining_nodes]
            for node in remaining_nodes:
                assert node in result_file
        else:
            assert "A.C.Instance2" not in result_file
            for node in remaining_nodes:
                assert node in result_file
