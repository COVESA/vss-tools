# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


@pytest.mark.parametrize(
    "filename, error",
    [
        ("test_single_level.vspec", "Invalid key value: A=None"),
        ("test_string_as_child.vspec", "Invalid key value: A=string"),
    ],
)
def test_error(tmp_path, filename, error):
    spec = HERE / filename
    output = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert error in log.read_text() or error in process.stderr
