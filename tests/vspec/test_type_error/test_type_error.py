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
    log = tmp_path / "log.txt"

    cmd = f"vspec --log-file {log} export json --pretty -u {TEST_UNITS} -q {TEST_QUANT}"
    if types_file:
        cmd += f" --types {HERE / types_file}"
    if types_out_file:
        cmd += f" --types-output {tmp_path / types_out_file}"
    if overlay_file:
        cmd += f" -l {HERE / overlay_file}"
    cmd += f" --vspec {vspec_file} --output {out}"

    process = subprocess.run(cmd.split())
    assert process.returncode != 0
    log_content = log.read_text()
    assert "has 1 model" in log_content
    assert "CRITICAL" in log_content


@pytest.mark.parametrize("vspec_file", [("branch_wrong_case.vspec"), ("sensor_wrong_case.vspec")])
def type_case_sensitive(vspec_file: str, tmp_path):
    vspec_file = HERE / vspec_file
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json --pretty --vspec {vspec_file} --output {out}"
    process = subprocess.run(cmd.split())
    assert process.returncode != 0
    assert "Unknown type" in log.read_text()


@pytest.mark.parametrize(
    "vspec_file",
    [
        ("branch_in_signal.vspec"),
    ],
)
def test_scope_error(vspec_file: str, tmp_path):
    vspec_file = HERE / vspec_file
    out = tmp_path / "out.json"
    log = tmp_path / "log.txt"
    cmd = f"vspec --log-file {log} export json --pretty -u {TEST_UNITS}"
    cmd += f" -q {TEST_QUANT} --vspec {vspec_file} --output {out}"
    process = subprocess.run(cmd.split())
    assert process.returncode != 0
    log_content = log.read_text()
    assert "Invalid nodes=1" in log_content
    assert "A.UInt8.CCC" in log_content
