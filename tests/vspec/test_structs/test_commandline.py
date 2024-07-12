# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import os


from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def test_error_when_data_types_file_is_missing(tmp_path):
    otypes = HERE / "output_types_file.json"
    spec = HERE / "test.vspec"
    output = tmp_path / "output.json"
    cmd = f"vspec2x json -u {TEST_UNITS} --types-output {otypes} --vspec {spec} --output {output}"
    env = os.environ.copy()
    env["COLUMNS"] = "200"
    process = subprocess.run(
        cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0
    assert (
        "raise ArgumentException"
        in process.stderr
    )


@pytest.mark.parametrize("format", ["binary", "franca", "graphql"])
def test_error_with_non_compatible_formats(format, tmp_path):
    otypes = HERE / "output_types_file.json"
    spec = HERE / "test.vspec"
    output = tmp_path / "output.json"
    types = HERE / "VehicleDataTypes.vspec"
    cmd = f"vspec2x {format} -u {TEST_UNITS} --types {types} --types-output {otypes} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "No such option: --types" in process.stderr


@pytest.mark.parametrize("format", ["ddsidl"])
def test_error_with_ot(format, tmp_path):
    otypes = HERE / "output_types_file.json"
    spec = HERE / "test.vspec"
    output = tmp_path / "output.json"
    types = HERE / "VehicleDataTypes.vspec"
    cmd = f"vspec2x {format} -u {TEST_UNITS} --types {types} --types-output {otypes} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "No such option: --types-output" in process.stderr
