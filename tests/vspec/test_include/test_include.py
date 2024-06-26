# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import subprocess
import filecmp

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def test_include(tmp_path):
    spec = HERE / "test.vspec"
    output = tmp_path / "out.json"
    expected = HERE / "expected.json"
    cmd = f"vspec2json -u {TEST_UNITS} --json-pretty {spec} {output}"
    subprocess.run(cmd.split(), check=True)
    filecmp.cmp(output, expected)


def test_error(tmp_path):
    spec = HERE / "test_error.vspec"
    output = tmp_path / "out.json"
    cmd = f"vspec2json -u {TEST_UNITS} --json-pretty {spec} {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0

    print(process.stdout)
    assert "WARNING  No branch matching" in process.stdout
    assert "Exception: Invalid VSS model" in process.stderr
