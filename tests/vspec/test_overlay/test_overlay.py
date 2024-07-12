# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import os
from pathlib import Path
import subprocess
import filecmp

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"


# Only running json exporter, overlay-functionality should be independent
# of selected exporter
def run_overlay(overlay_prefix, tmp_path):
    spec = HERE / "test.vspec"
    overlay_name = f"overlay_{overlay_prefix}.vspec"
    overlay = HERE / overlay_name
    output = tmp_path / "out.json"
    cmd = (
        f"vspec2x json --pretty -u {TEST_UNITS} -e dbc --vspec {spec} -l {overlay} --output {output}"
    )
    subprocess.run(cmd.split(), check=True)
    expected = HERE / f"expected_{overlay_prefix}.json"
    assert filecmp.cmp(output, expected)


def test_explicit_overlay(tmp_path):
    run_overlay("explicit_branches", tmp_path)


def test_implicit_overlay(tmp_path):
    run_overlay("implicit_branches", tmp_path)


def test_no_datatype(tmp_path):
    run_overlay("no_datatype", tmp_path)


def test_no_type(tmp_path):
    run_overlay("no_type", tmp_path)


def test_overlay_error(tmp_path):
    overlay = HERE / "overlay_error.vspec"
    output = tmp_path / "out.json"
    spec = HERE / "test.vspec"
    cmd = f"vspec2x json --pretty -u {TEST_UNITS} -l {overlay} --vspec {spec} --output {output}"
    env = os.environ.copy()
    env["COLUMNS"] = "300"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0
    assert "need to have a datatype declared" in process.stdout


def test_overlay_branch_error(tmp_path):
    overlay = HERE / "overlay_implicit_branch_no_description.vspec"
    output = tmp_path / "out.json"
    spec = HERE / "test.vspec"
    cmd = f"vspec2x json --pretty -u {TEST_UNITS} -l {overlay} --vspec {spec} --output {output}"

    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "Invalid VSS element AB, must have description" in process.stdout
