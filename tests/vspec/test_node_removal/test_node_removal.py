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


import os
import shlex
from typing import Optional

import pytest

import vspec2binary  # noqa: F401
import vspec2csv  # noqa: F401
import vspec2ddsidl  # noqa: F401
import vspec2franca  # noqa: F401
import vspec2graphql  # noqa: F401
import vspec2json  # noqa: F401
import vspec2jsonschema  # noqa: F401
import vspec2protobuf  # noqa: F401
import vspec2yaml  # noqa: F401


# HELPERS


def get_cla(test_file: str, out_file: str, overlay: Optional[str]):
    if overlay:
        return (
                test_file + " " + out_file + " -o " + overlay + " -u ../test_units.yaml"
        )
    else:
        return test_file + " " + out_file + " -u ../test_units.yaml"


# FIXTURES


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


@pytest.fixture(scope="function", autouse=True)
def delete_files(change_test_dir):
    yield None
    os.system("rm -f out.*")


# INTEGRATION TESTS


@pytest.mark.usefixtures("change_test_dir")
@pytest.mark.parametrize(
    "exporter, out_file, overlay",
    [
        ("vspec2binary", "out.bin", None),
        ("vspec2csv", "out.csv", None),
        ("vspec2ddsidl", "out.idl", None),
        ("vspec2franca", "out.fidl", None),
        ("vspec2graphql", "out.graphql", None),
        ("vspec2json", "out.json", None),
        ("vspec2jsonschema", "out.jsonschema", None),
        ("vspec2protobuf", "out.pb", None),
        ("vspec2yaml", "out.yaml", None),
        ("vspec2binary", "out.bin", "test_files/test_del_node_overlay.vspec"),
        ("vspec2csv", "out.csv", "test_files/test_del_node_overlay.vspec"),
        ("vspec2ddsidl", "out.idl", "test_files/test_del_node_overlay.vspec"),
        ("vspec2franca", "out.fidl", "test_files/test_del_node_overlay.vspec"),
        ("vspec2graphql", "out.graphql", "test_files/test_del_node_overlay.vspec"),
        ("vspec2json", "out.json", "test_files/test_del_node_overlay.vspec"),
        (
            "vspec2jsonschema",
            "out.jsonschema",
            "test_files/test_del_node_overlay.vspec",
        ),
        ("vspec2protobuf", "out.pb", "test_files/test_del_node_overlay.vspec"),
        ("vspec2yaml", "out.yaml", "test_files/test_del_node_overlay.vspec"),
    ],
)
def test_deleted_node(exporter: str, out_file: str, overlay: Optional[str]):
    test_file: str
    if overlay:
        test_file = "test_files/test.vspec"
    else:
        test_file = "test_files/test_deleted_node.vspec"

    clas = shlex.split(
        get_cla(test_file, out_file, overlay)
    )  # get command line arguments without the executable

    eval(f"{exporter}.main({clas})")
    with open(out_file) as f:
        result = f.read()

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


@pytest.mark.usefixtures("change_test_dir")
@pytest.mark.parametrize(
    "exporter, out_file, overlay",
    [
        ("vspec2binary", "out.bin", None),
        ("vspec2csv", "out.csv", None),
        ("vspec2ddsidl", "out.idl", None),
        ("vspec2franca", "out.fidl", None),
        ("vspec2graphql", "out.graphql", None),
        ("vspec2json", "out.json", None),
        ("vspec2jsonschema", "out.jsonschema", None),
        ("vspec2protobuf", "out.pb", None),
        ("vspec2yaml", "out.yaml", None),
        ("vspec2binary", "out.bin", "test_files/test_del_branch_overlay.vspec"),
        ("vspec2csv", "out.csv", "test_files/test_del_branch_overlay.vspec"),
        ("vspec2ddsidl", "out.idl", "test_files/test_del_branch_overlay.vspec"),
        ("vspec2franca", "out.fidl", "test_files/test_del_branch_overlay.vspec"),
        ("vspec2graphql", "out.graphql", "test_files/test_del_branch_overlay.vspec"),
        ("vspec2json", "out.json", "test_files/test_del_branch_overlay.vspec"),
        (
            "vspec2jsonschema",
            "out.jsonschema",
            "test_files/test_del_branch_overlay.vspec",
        ),
        ("vspec2protobuf", "out.pb", "test_files/test_del_branch_overlay.vspec"),
        ("vspec2yaml", "out.yaml", "test_files/test_del_branch_overlay.vspec"),
    ],
)
def test_deleted_branch(exporter: str, out_file: str, overlay: Optional[str]):
    test_file: str
    if overlay:
        test_file = "test_files/test.vspec"
    else:
        test_file = "test_files/test_deleted_branch.vspec"
    clas = shlex.split(get_cla(test_file, out_file, overlay))

    eval(f"{exporter}.main({clas})")
    result_file: str
    with open(out_file) as f:
        result_file = f.read()

    remaining_nodes = ["A.Float", "A.Int16", "A.String", "A.StringArray"]

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

    else:
        assert "A.B" not in result_file
        for node in remaining_nodes:
            assert node in result_file
