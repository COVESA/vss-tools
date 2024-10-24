# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import filecmp
import pathlib
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / "test_units.yaml"
TEST_QUANT = HERE / "test_quantities.yaml"
DEFAULT_TEST_FILE = "test.vspec"


def default_directories() -> list:
    directories = []
    for path in HERE.iterdir():
        if path.is_dir():
            if list(path.rglob(DEFAULT_TEST_FILE)):
                # Exclude directories with custom made python file
                if not list(path.rglob("*.py")):
                    directories.append(path)
    return directories


# Use directory name as test name
def idfn(directory: pathlib.PosixPath):
    return directory.name


def run_exporter(directory, exporter, tmp_path):
    vspec = directory / DEFAULT_TEST_FILE
    types = directory / "types.vspec"
    output = tmp_path / f"out.{exporter}"
    expected = directory / f"expected.{exporter}"
    if not expected.exists():
        # If you want find directory/exporter combinations not yet covered enable the assert
        # assert False, f"Folder {expected} not found"
        return
    cmd = f"vspec export {exporter} -u {TEST_UNITS} -q {TEST_QUANT} --vspec {vspec} "
    if types.exists():
        cmd += f" --types {types}"
    if exporter in ["apigear"]:
        cmd += f" --output-dir {output}"
    elif exporter in ["samm"]:
        cmd += f" --target-folder {output}"
    else:
        cmd += f" --output {output}"
    subprocess.run(cmd.split(), check=True)
    if exporter in ["apigear", "samm"]:
        dcmp = filecmp.dircmp(output, expected)
        assert not (dcmp.diff_files or dcmp.left_only or dcmp.right_only)
    else:
        assert filecmp.cmp(output, expected)


@pytest.mark.parametrize("directory", default_directories(), ids=idfn)
def test_exporters(directory, tmp_path):
    # Run all "supported" exporters, i.e. not those in contrib
    # Exception is "binary", as it is assumed output may vary depending on target
    exporters = ["apigear", "json", "jsonschema", "ddsidl", "csv", "yaml", "franca", "graphql", "go", "samm"]

    for exporter in exporters:
        run_exporter(directory, exporter, tmp_path)
