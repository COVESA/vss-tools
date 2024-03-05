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

import pytest
import yaml

import vspec2json
import vspec2yaml

# HELPERS


def get_cla(exporter_path: str, test_file: str, out_file: str):
    return exporter_path + " " + test_file + " " + out_file


# FIXTURES


@pytest.fixture
def change_test_dir(request, monkeypatch):
    # To make sure we run from test directory
    monkeypatch.chdir(request.fspath.dirname)


# UNIT TESTS
# ToDo

# INTEGRATION TESTS


@pytest.mark.usefixtures("change_test_dir")
@pytest.mark.parametrize(
    "exporter_path, out_file",
    [
        ("../../../vspec2yaml.py", "out.yaml"),
        # ("../../../vspec2json.py", "out.json"),
    ],
)
def test_exporter(caplog: pytest.LogCaptureFixture, exporter_path: str, out_file: str):
    test_file: str = "test_files/test.vspec"

    clas = shlex.split(get_cla(exporter_path, test_file, out_file))
    print(f"clas: {clas}")
    if "yaml" in exporter_path:
        vspec2yaml.main(clas[1:])
        result_dict: dict
        with open(out_file) as f:
            result_dict = yaml.load(f, Loader=yaml.FullLoader)

        validation_dict: dict
        with open("validation_files/validation.yaml") as f:
            validation_dict = yaml.load(f, Loader=yaml.FullLoader)

        assert result_dict.keys() == validation_dict.keys()

    elif "json" in exporter_path:
        vspec2json.main(clas[1:])
        # ToDo json and other exporters


@pytest.mark.usefixtures("change_test_dir")
@pytest.mark.parametrize(
    "exporter_path, out_file",
    [
        ("../../../vspec2yaml.py", "out.yaml"),
        # ("../../../vspec2json.py", "out.json"),
    ],
)
def test_deleted_node(
    caplog: pytest.LogCaptureFixture, exporter_path: str, out_file: str
):
    test_file: str = "test_files/test_deleted_node.vspec"
    clas = shlex.split(get_cla(exporter_path, test_file, out_file))

    if "yaml" in exporter_path:
        vspec2yaml.main(clas[1:])
        result_file: dict = {}
        with open(out_file) as f:
            result_file = yaml.load(f, Loader=yaml.FullLoader)
        assert "A.B.Int32" not in result_file.keys()

    elif "json" in exporter_path:
        # ToDo json and other exporters
        pass


@pytest.mark.usefixtures("change_test_dir")
@pytest.mark.parametrize(
    "exporter_path, out_file",
    [
        ("../../../vspec2yaml.py", "out.yaml"),
        # ("../../../vspec2json.py", "out.json"),
    ],
)
def test_deleted_branch(
    caplog: pytest.LogCaptureFixture, exporter_path: str, out_file: str
):
    test_file: str = "test_files/test_deleted_branch.vspec"
    clas = shlex.split(get_cla(exporter_path, test_file, out_file))

    if "yaml" in exporter_path:
        vspec2yaml.main(clas[1:])
        result_file: dict = {}
        with open(out_file) as f:
            result_file = yaml.load(f, Loader=yaml.FullLoader)
        assert "A.B" not in result_file.keys()

    elif "json" in exporter_path:
        # ToDo json and other exporters
        pass
