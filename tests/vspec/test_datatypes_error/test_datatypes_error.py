# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def test_datatype_error(tmp_path):
    spec = HERE / "test.vspec"
    output = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = (
        f"vspec --log-file {log} export json --pretty -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    )
    process = subprocess.run(cmd.split())
    assert process.returncode != 0

    print(process.stdout)
    assert "'uint7' is not a valid datatype" in log.read_text()


def test_datatype_branch(tmp_path):
    spec = HERE / "test_datatype_branch.vspec"
    output = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json --pretty -u {TEST_UNITS} -q {TEST_QUANT}"
    cmd += f" --vspec {spec} --output {output} --strict"
    process = subprocess.run(cmd.split())
    assert process.returncode != 0
    assert "Unknown extra attribute: 'A':'datatype'" in log.read_text()
