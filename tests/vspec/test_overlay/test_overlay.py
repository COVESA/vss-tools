# Copyright (c) 2022 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0
import filecmp
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


# Only running json exporter, overlay-functionality should be independent
# of selected exporter
def run_overlay(overlay_prefix, tmp_path):
    spec = HERE / "test.vspec"
    overlay_name = f"overlay_{overlay_prefix}.vspec"
    overlay = HERE / overlay_name
    output = tmp_path / "out.json"
    cmd = f"vspec export json --pretty -u {TEST_UNITS} -q {TEST_QUANT}"
    cmd += f" -e dbc --vspec {spec} -l {overlay} --output {output}"
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
    cmd = f"vspec export json --pretty -u {TEST_UNITS}"
    cmd += f" -q {TEST_QUANT} -l {overlay} --vspec {spec} --output {output}"
    env = os.environ.copy()
    env["COLUMNS"] = "300"
    process = subprocess.run(cmd.split(), capture_output=True, text=True, env=env)
    assert process.returncode != 0
    print(process.stdout)
    assert "'A.SignalXXXX' has 1 model error(s)" in process.stdout
    assert "'type': 'missing'" in process.stdout
    assert "datatype" in process.stdout


def test_overlay_branch_error(tmp_path):
    overlay = HERE / "overlay_implicit_branch_no_description.vspec"
    output = tmp_path / "out.json"
    spec = HERE / "test.vspec"
    cmd = f"vspec export json --pretty -u {TEST_UNITS}"
    cmd += f" -q {TEST_QUANT} -l {overlay} --vspec {spec} --output {output}"

    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    print(process.stdout)
    assert "'A.AB' has 1 model error(s)" in process.stdout
    assert "'type': 'missing'" in process.stdout
    assert "description" in process.stdout
