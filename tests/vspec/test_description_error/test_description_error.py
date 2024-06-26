# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import pytest
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


@pytest.mark.parametrize(
    "vspec_file, type_file, type_out_file",
    [
        ("no_description_branch.vspec", None, None),
        ("no_description_signal.vspec", None, None),
        ("correct.vspec", "no_description_type_branch.vspec", "ot.json"),
        ("correct.vspec", "no_description_type_struct.vspec", "ot.json"),
        ("correct.vspec", "no_description_type_property.vspec", "ot.json"),
    ],
)
def test_description_error(
    vspec_file: str, type_file: str, type_out_file: str, tmp_path
):
    output = tmp_path / "out.json"
    cmd = f"vspec2json --json-pretty -u {TEST_UNITS}"
    if type_file:
        cmd += f" -vt {HERE / type_file}"
    if type_out_file:
        cmd += f" -ot {tmp_path / type_out_file}"
    cmd += f" {HERE / vspec_file} {output}"

    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "Invalid VSS element" in process.stdout
