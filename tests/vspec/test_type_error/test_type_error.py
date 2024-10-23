# Copyright (c) 2023 Contributors to COVESA
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
VSS_TOOLS_ROOT = (HERE / ".." / ".." / "..").absolute()
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


@pytest.mark.parametrize(
    "vspec_file, types_file, types_out_file, overlay_file",
    [
        ("no_type_branch.vspec", None, None, None),
        ("no_type_signal.vspec", None, None, None),
        ("correct.vspec", None, None, "no_type_overlay.vspec"),
        ("correct.vspec", "no_type_struct.vspec", "ot.json", None),
        ("correct.vspec", "no_type_property.vspec", "ot.json", None),
    ],
)
def test_description_error(vspec_file: str, types_file, types_out_file, overlay_file, tmp_path):
    vspec_file = HERE / vspec_file
    out = tmp_path / "out.json"

    cmd = f"vspec export json --pretty -u {TEST_UNITS} -q {TEST_QUANT}"
    if types_file:
        cmd += f" --types {HERE / types_file}"
    if types_out_file:
        cmd += f" --types-output {tmp_path / types_out_file}"
    if overlay_file:
        cmd += f" -l {HERE / overlay_file}"
    cmd += f" --vspec {vspec_file} --output {out}"

    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    print(process.stdout)
    assert "has 1 model" in process.stdout
    assert "CRITICAL" in process.stdout


@pytest.mark.parametrize("vspec_file", [("branch_wrong_case.vspec"), ("sensor_wrong_case.vspec")])
def type_case_sensitive(vspec_file: str, tmp_path):
    vspec_file = HERE / vspec_file
    out = tmp_path / "out.json"
    cmd = f"vspec export json --pretty --vspec {vspec_file} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "Unknown type" in process.stdout


@pytest.mark.parametrize(
    "vspec_file",
    [
        ("branch_in_signal.vspec"),
    ],
)
def test_scope_error(vspec_file: str, tmp_path):
    vspec_file = HERE / vspec_file
    out = tmp_path / "out.json"
    cmd = f"vspec export json --pretty -u {TEST_UNITS}"
    cmd += f" -q {TEST_QUANT} --vspec {vspec_file} --output {out}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "Invalid nodes=1" in process.stdout
    assert "A.UInt8.CCC" in process.stdout
