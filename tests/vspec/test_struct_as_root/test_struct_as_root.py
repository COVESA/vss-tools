# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


def test_struct_as_root(tmp_path):
    struct = HERE / "struct1.vspec"
    spec = HERE / "test.vspec"
    output = tmp_path / "out.csv"
    cmd = f"vspec export csv --types {struct} -u {TEST_UNITS} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "Root node Struct1 is not of branch type" in process.stdout
