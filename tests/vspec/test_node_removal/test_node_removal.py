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


def get_cla(test_file: str, out_file: str):
    return test_file + " " + out_file


# FIXTURES


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


# INTEGRATION TESTS


@pytest.mark.usefixtures("change_test_dir")
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
def test_deleted_node(exporter: str, out_file: str):
    test_file: str = "test_files/test_deleted_node.vspec"
    clas = shlex.split(
        get_cla(test_file, out_file)
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

    # remove all generated files
    os.system(f"rm -f {out_file}")


@pytest.mark.usefixtures("change_test_dir")
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
def test_deleted_branch(exporter: str, out_file: str):
    test_file: str = "test_files/test_deleted_branch.vspec"
    clas = shlex.split(get_cla(test_file, out_file))

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

    # remove all generated files
    os.system(f"rm -f {out_file}")
